from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import create_tables, SessionLocal
from backend.seed import seed_database
from backend.routes.regions import router as regions_router
from backend.routes.financial import router as financial_router
from backend.routes.simulation import router as simulation_router


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


@app.get("/health")
def health_check():
    return {"status": "ok"}
