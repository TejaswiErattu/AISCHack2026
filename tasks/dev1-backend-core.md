# Developer 1: Backend Core Engine

**Scope**: FastAPI server, database, climate engine, financial translator, all REST endpoints, mock data layer.
**Independence**: Fully standalone. All endpoints testable via pytest + httpx without frontend or AI layer.
**Convention**: Every subtask ends with tests covering happy path + edge cases before moving on.

---

## Task 1: Project Scaffold & Configuration

### 1.1 FastAPI project structure
- Create `backend/` package with `__init__.py`
- Create `backend/main.py` with FastAPI app, CORS middleware (allow all origins for dev), and health check endpoint `GET /health`
- Create `backend/config.py` — loads `.env` via `pydantic-settings` (`DATABASE_URL`, `NOAA_API_KEY`, `DEMO_MODE`)
- Create `requirements.txt`: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `python-dotenv`, `httpx`, `pytest`, `pytest-asyncio`, `httpx`

**Tests after 1.1:**
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] App starts on `uvicorn backend.main:app --port 8000` without errors
- [ ] Config loads from `.env` and falls back to defaults when `.env` is missing
- [ ] CORS headers present in response

### 1.2 SQLite database setup
- Create `backend/models/database.py`:
  - SQLAlchemy engine + `SessionLocal` from `DATABASE_URL`
  - `get_db()` dependency (yields session, closes on teardown)
  - `Base = declarative_base()`
- Create `backend/models/models.py` — ORM models:
  - `Region`: region_id (PK str), name, lat, lng, primary_crop, base_loan_rate, base_pd, base_premium
  - `ClimateSnapshot`: snapshot_id (PK str), region_id (FK), temperature_anomaly, drought_index, rainfall_anomaly, ndvi_score, soil_moisture, yield_stress_score, timestamp
  - `FinancialOutput`: output_id (PK str), region_id (FK), snapshot_id (FK), interest_rate, probability_of_default, insurance_premium, repayment_flexibility, baseline_rate, timestamp
  - `SimulationRun`: run_id (PK str), region_id (FK), input_overrides (JSON), stress_score, financial_outputs (JSON), narrative, panel_context, created_at
- Create `backend/models/schemas.py` — Pydantic response models:
  - `RegionResponse`, `ClimateResponse`, `StressResponse`, `FinancialResponse`, `ComparisonResponse`, `SystemDetails`, `SimulateRequest`, `SimulateResponse`
- Add `create_tables()` function that runs `Base.metadata.create_all()`

**Tests after 1.2:**
- [ ] Tables created successfully in a temp SQLite DB
- [ ] All ORM models can INSERT and SELECT correctly
- [ ] Pydantic schemas validate correct data and reject malformed data
- [ ] `get_db()` yields a session and closes it
- [ ] FK constraints enforced (invalid region_id rejected)
- [ ] JSON fields on `SimulationRun` serialize/deserialize correctly

### 1.3 Seed data script
- Create `backend/seed.py` — populates 20+ US agricultural regions with realistic data:
  - Central Valley CA, Midwest Corn Belt (Iowa), Texas Panhandle, Columbia Basin WA, Mississippi Delta, San Joaquin Valley CA, Nebraska Sandhills, Kansas Wheat Belt, Sacramento Valley CA, Florida Citrus Belt, Willamette Valley OR, Red River Valley ND, Yakima Valley WA, Imperial Valley CA, Snake River Plain ID, Ozark Plateau MO, Bluegrass Region KY, Palouse WA, Rio Grande Valley TX, Shenandoah Valley VA
  - Each region has: lat/lng, primary_crop, base_loan_rate (4.5–6.5%), base_pd (0.03–0.08), base_premium (800–1600)
- Seed baseline `FinancialOutput` rows per region (the "old system" static rates — base_loan_rate + 1.0 to 2.0)
- Seed baseline `ClimateSnapshot` rows per region with seasonal-norm values
- Script is idempotent (check before insert, or truncate + re-seed)

**Tests after 1.3:**
- [ ] Running seed twice does not create duplicates
- [ ] All 20+ regions present with valid coordinates (lat -90..90, lng -180..180)
- [ ] All base financial values within realistic ranges
- [ ] Baseline climate snapshots have reasonable seasonal values (no zeros, no extremes)
- [ ] Each region has exactly one baseline FinancialOutput and one baseline ClimateSnapshot

---

## Task 2: Climate Data Service

### 2.1 Mock climate data layer
- Create `backend/services/mock_data.py`:
  - Dict of all 20+ regions → realistic climate snapshots (temperature_anomaly, drought_index, rainfall_anomaly, ndvi_score, soil_moisture)
  - Values vary by region (e.g., Central Valley hotter/drier than Willamette Valley)
  - `get_mock_climate(region_id: str) -> dict` function
- Values must be realistic and internally consistent per region

**Tests after 2.1:**
- [ ] `get_mock_climate()` returns data for all seeded regions
- [ ] Returns `None` or raises for unknown region_id
- [ ] All values within valid ranges: temperature_anomaly (-5 to +8), drought_index (0–100), rainfall_anomaly (-80 to +80), ndvi_score (0–100), soil_moisture (0–100)
- [ ] Different regions return different values (not all identical)

### 2.2 NOAA API integration
- Create `backend/services/noaa_client.py`:
  - `async fetch_noaa_data(lat, lng, api_key) -> dict` using `httpx`
  - Calls NOAA Climate Data Online (CDO) API for recent temperature and precipitation
  - Normalize raw NOAA values to our index scales (0–100)
  - Timeout of 5s, graceful error handling
- Does NOT need to work perfectly — the mock fallback is the reliable path

**Tests after 2.2:**
- [ ] Function returns normalized dict with expected keys when mocked NOAA response given
- [ ] Handles NOAA API timeout gracefully (returns None, does not crash)
- [ ] Handles NOAA 429 rate limit response gracefully
- [ ] Handles malformed NOAA response (missing fields) gracefully
- [ ] Handles network error gracefully

### 2.3 Climate data orchestrator
- Create `backend/services/climate_data.py`:
  - `async get_climate_data(region_id, lat, lng, db) -> dict`
  - Logic: if `DEMO_MODE=true` → use mock data directly
  - Else: try NOAA API → on failure, fall back to mock data
  - Always returns a dict with all 5 climate fields
  - Log which source was used (real vs mock)

**Tests after 2.3:**
- [ ] Returns mock data when `DEMO_MODE=true`
- [ ] Returns NOAA data when NOAA succeeds and `DEMO_MODE=false`
- [ ] Falls back to mock when NOAA fails and `DEMO_MODE=false`
- [ ] Return dict always has all 5 required keys
- [ ] Logs indicate which data source was used
- [ ] Works for all 20+ seeded regions

---

## Task 3: Yield Stress Engine

### 3.1 Core formula implementation
- Create `backend/services/climate_engine.py`:
  - `compute_yield_stress(temperature_anomaly, drought_index, rainfall_anomaly, ndvi_score, soil_moisture) -> float`
  - Formula from PRD Section 4.3:
    ```
    yield_stress_score = (
      0.30 * heat_stress_index +
      0.25 * drought_index +
      0.20 * rainfall_anomaly_index +
      0.15 * (100 - ndvi_score) +
      0.10 * soil_moisture_deficit
    ) / 1.0
    ```
  - `heat_stress_index`: convert temperature_anomaly to 0–100 (e.g., -3°C→0, +5°C→100, linear)
  - `rainfall_anomaly_index`: convert -80..+80% to 0–100 stress (both extremes are stressful; deviation from 0 = stress)
  - `soil_moisture_deficit`: `100 - soil_moisture`
  - Output clamped to 0–100

**Tests after 3.1:**
- [ ] All-normal inputs → low stress (< 30)
- [ ] All-extreme inputs → high stress (> 80)
- [ ] Perfect conditions (no anomaly, high NDVI, good moisture) → stress near 0
- [ ] Single-factor dominance: maxing out just heat stress with others normal → stress between 25–35
- [ ] Output always clamped 0–100 regardless of input extremes
- [ ] Weights sum to 1.0 validation
- [ ] Negative temperature anomaly (cooling) → low heat stress contribution
- [ ] Both extreme rainfall surplus and deficit produce high rainfall stress
- [ ] Boundary values: all inputs at 0, all at 100, all at 50
- [ ] Float precision: fractional inputs produce correct fractional output

---

## Task 4: Financial Risk Translator

### 4.1 Core translation formulas
- Create `backend/services/financial_translator.py`:
  - `translate_financial(base_rate, base_pd, base_premium, yield_stress_score) -> dict`
  - Formulas from PRD Section 4.4:
    ```
    PD = base_pd + (yield_stress_score / 100) * 0.25
    interest_rate = base_rate + (PD * 0.08 * 100)
    insurance_premium = base_premium * (1 + yield_stress_score / 100)
    repayment_flexibility = 100 - yield_stress_score
    ```
  - Clamp all outputs to sane ranges:
    - interest_rate: 3.0% – 15.0%
    - PD: 0.01 – 0.50
    - insurance_premium: base * 0.8 – base * 3.0
    - repayment_flexibility: 0 – 100

**Tests after 4.1:**
- [ ] Zero stress → outputs near base values
- [ ] Max stress (100) → outputs at upper bounds
- [ ] Mid stress (50) → outputs proportionally between min and max
- [ ] Clamping works: artificially high stress doesn't produce interest_rate > 15%
- [ ] Different base values produce different outputs (base_rate 4.5 vs 6.5)
- [ ] All dict keys present in output: `interest_rate`, `probability_of_default`, `insurance_premium`, `repayment_flexibility`
- [ ] Negative stress score (shouldn't happen but defensive) → clamped to 0 behavior
- [ ] Insurance premium never below 80% of base (floor protection)

---

## Task 5: REST API Endpoints

### 5.1 Region endpoints
- Create `backend/routes/regions.py`:
  - `GET /regions` → list of all regions (id, name, lat, lng, primary_crop)
  - `GET /region/{region_id}/climate` → current climate data for region
  - `GET /region/{region_id}/stress` → yield stress score + breakdown
- Wire routes into `main.py`

**Tests after 5.1:**
- [ ] `GET /regions` returns 20+ regions
- [ ] `GET /regions` response matches `List[RegionResponse]` schema
- [ ] `GET /region/central-valley-ca/climate` returns valid climate data
- [ ] `GET /region/nonexistent/climate` returns 404
- [ ] `GET /region/central-valley-ca/stress` returns float 0–100
- [ ] Stress endpoint returns breakdown (which factors contribute most)

### 5.2 Financial endpoints
- Create `backend/routes/financial.py`:
  - `GET /region/{region_id}/financial` → all financial outputs
  - `GET /region/{region_id}/comparison` → old system vs TerraLend side-by-side
- Wire routes into `main.py`

**Tests after 5.2:**
- [ ] Financial endpoint returns all fields: interest_rate, probability_of_default, insurance_premium, repayment_flexibility, baseline_rate
- [ ] Comparison endpoint returns `old_system` and `terralend` objects
- [ ] Old system values are static (don't change with climate data)
- [ ] TerraLend values reflect current climate data
- [ ] 404 for invalid region_id on both endpoints
- [ ] Financial values are within clamped ranges

### 5.3 Simulation endpoint
- Create `backend/routes/simulation.py`:
  - `POST /simulate` — accepts `SimulateRequest`:
    ```json
    {
      "region_id": "central-valley-ca",
      "temperature_delta": 2.5,
      "drought_index": 70,
      "rainfall_anomaly": -40
    }
    ```
  - Merges overrides with current climate data for that region
  - Recomputes stress + financial outputs
  - Returns `SimulateResponse` with full recalculated values + deltas from baseline
- Wire route into `main.py`

**Tests after 5.3:**
- [ ] Simulate with no overrides returns same as baseline
- [ ] Simulate with temperature_delta +5 returns higher stress/rate
- [ ] Simulate with drought_index 100 returns near-max stress
- [ ] Response includes deltas (new value - baseline value) for stress and all financial fields
- [ ] 404 for invalid region_id
- [ ] Partial overrides work (only temperature_delta, others use current values)
- [ ] Extreme overrides don't crash (temperature_delta +100 → clamped gracefully)
- [ ] Response includes both the new values and the baseline values

### 5.4 Wire all routes + startup
- Update `backend/main.py`:
  - Include all routers: regions, financial, simulation
  - Add startup event: create tables + run seed
  - Add CORS middleware for frontend dev
- Create `run.py` or add uvicorn config for easy startup

**Tests after 5.4:**
- [ ] Full integration test: start app → seed runs → `GET /regions` returns data → `GET /region/X/climate` works → `POST /simulate` works
- [ ] CORS preflight requests pass
- [ ] Server starts clean from empty database (tables created + seeded)
- [ ] Server starts clean with existing database (idempotent seed)
- [ ] All endpoints return proper JSON content-type
- [ ] Error responses follow consistent format `{"detail": "..."}`

---

## Task 6: API Contract Documentation

### 6.1 Response shape documentation
- Create `backend/API_CONTRACTS.md` documenting exact response shapes for every endpoint
- This is the contract that Developer 2 (Frontend) uses to build their mock API layer
- Include example responses for each endpoint with realistic values

**Deliverable:** JSON examples for:
- `GET /regions`
- `GET /region/{id}/climate`
- `GET /region/{id}/stress`
- `GET /region/{id}/financial`
- `GET /region/{id}/comparison`
- `POST /simulate` (request + response)

**No tests — documentation only. But verify each example against actual endpoint output.**

---

## Summary Checklist

- [ ] Task 1: Scaffold, DB, Seed Data
- [ ] Task 2: Climate Data Service (mock + NOAA + orchestrator)
- [ ] Task 3: Yield Stress Engine
- [ ] Task 4: Financial Risk Translator
- [ ] Task 5: All REST Endpoints
- [ ] Task 6: API Contract Documentation (for Frontend dev to consume)
