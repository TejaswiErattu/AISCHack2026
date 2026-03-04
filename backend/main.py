import hashlib
import json
import os
import time as _time
from contextlib import asynccontextmanager
from pathlib import Path

import boto3
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import create_tables, SessionLocal
from backend.seed import seed_database
from backend.routes.regions import router as regions_router
from backend.routes.financial import router as financial_router
from backend.routes.simulation import router as simulation_router
from backend.routes.narrative import router as narrative_router

# Load .env from the backend directory
load_dotenv(Path(__file__).parent / ".env")

_session = boto3.Session(
    profile_name=os.getenv("AWS_PROFILE", "terralend"),
    region_name=os.getenv("AWS_REGION", "us-west-2"),
)
bedrock = _session.client("bedrock-runtime")

BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0")

# Proposal response cache: hash(request_body) -> (timestamp, response)
_proposal_cache: dict[str, tuple[float, dict]] = {}
_PROPOSAL_CACHE_TTL = 600  # 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and seed data."""
    create_tables()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(title="TerraLend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(regions_router)
app.include_router(financial_router)
app.include_router(simulation_router)
app.include_router(narrative_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: dict = Body(...)):
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "system": request.get("system", ""),
            "messages": request.get("messages", []),
        })
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=body,
        )
        result = json.loads(response["body"].read())
        return {"text": result["content"][0]["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/region/{region_id}/proposal")
async def generate_proposal(region_id: str, request: dict = Body(...)):
    # Check proposal cache by hashing the request body
    cache_key = hashlib.sha256(
        json.dumps({"region_id": region_id, **request}, sort_keys=True).encode()
    ).hexdigest()

    if cache_key in _proposal_cache:
        ts, cached_response = _proposal_cache[cache_key]
        if _time.time() - ts < _PROPOSAL_CACHE_TTL:
            return cached_response

    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": "You are a senior agricultural loan underwriter. Generate a formal loan proposal memo in professional financial language.",
            "messages": [{
                "role": "user",
                "content": f"""Generate a formal agricultural loan proposal for:
Region: {request.get('region_name')}
Crop: {request.get('primary_crop')}
Yield Stress Score: {request.get('yield_stress_score')}/100
Interest Rate: {request.get('interest_rate')}%
Probability of Default: {request.get('probability_of_default')}%
Insurance Premium: ${request.get('insurance_premium')}/season
Heat Stress: +{request.get('temperature_anomaly')}°C above norm
Drought Index: {request.get('drought_index')}/100
NDVI Health: {request.get('ndvi_score')}/100

Include: executive summary, risk assessment, recommended terms, conditions, and climate risk disclosure. Professional tone. 400 words max."""
            }]
        })
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=body,
        )
        result = json.loads(response["body"].read())
        response_data = {"proposal": result["content"][0]["text"]}
        _proposal_cache[cache_key] = (_time.time(), response_data)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

