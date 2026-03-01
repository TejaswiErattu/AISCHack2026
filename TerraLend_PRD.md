# TerraLend — Adaptive Climate-Aware Lending Engine

**Technical Product Requirements Document (PRD)**
Version: v1.0 (Hackathon Draft)
Status: Active Working PRD

---

## 1. Product Overview

### 1.0 Executive Summary

Banks have been underwriting farm loans the same way for decades — credit scores, historical averages, regional risk tables. Static numbers for a world that's anything but static. TerraLend bridges two industries that have never meaningfully talked to each other: agricultural microclimate science and financial credit underwriting. Using real-time satellite vegetation data, soil moisture indices, and weather anomalies, TerraLend computes a live crop stress score for any US farm region — and instantly translates it into dynamic loan terms. Interest rates, probability of default, insurance premiums, and repayment schedules all update in real time as climate conditions shift. The same data, seen through two lenses: a loan officer gets clinical risk intelligence. A farmer gets plain-language transparency into why their rate changed. To also simulate, Drag a temperature slider. Trigger a drought. Watch the financial system respond — in seconds, not years. That's the bridge. Climate volatility is already repricing agricultural risk. TerraLend makes sure finance knows about it.

### 1.1 One-Line Summary

An AI-powered underwriting layer that ingests real-time microclimate data, models crop stress at regional resolution, and dynamically adjusts loan terms — bridging agricultural science and financial credit systems that have never meaningfully spoken to each other.

### 1.2 The Bridge

**Agricultural microclimate science ↔ Financial credit underwriting**

Today, banks underwrite farm loans using static historical averages, credit scores, and regional risk categories. They do not integrate satellite vegetation data, model soil stress in real time, or adjust loan risk dynamically based on live environmental signals.

TerraLend is the bridge layer that makes this possible. Remove the climate modeling and underwriting becomes static. Remove the finance layer and microclimate modeling has no economic consequence. The innovation lives entirely in the intersection.

### 1.3 Problem Statement

Farmers — particularly smallholder and independent operators — are among the most climate-exposed people on earth, yet the financial systems they depend on treat climate as a fixed background variable rather than a dynamic input. This creates three compounding failures:

- Banks price loans on yesterday's risk, not tomorrow's weather
- Farmers in high climate-volatility regions pay worse rates due to blunt regional categorization, not actual climate intelligence (MVP operates at region-level resolution; field-level parcel data is on the roadmap)
- When climate shocks hit, loan terms don't flex — farmers default on loans for reasons entirely outside their control

TerraLend reframes lending from **reactive** to **adaptive**.

### 1.4 Target Impact

- Give loan officers real-time, region-level climate intelligence at the point of underwriting (MVP), with a clear path to field-level parcel resolution
- Give farmers a transparent view of how environmental conditions affect their loan terms
- Demonstrate that climate science can directly improve financial equity for agricultural communities
- Establish a proof-of-concept for dynamic, climate-adjusting loan contracts
- Ensure adaptive pricing never punishes farmers at their most vulnerable — fairness guardrails are core, not optional

### 1.5 Why Now

- Climate volatility is accelerating — static underwriting models are increasingly inadequate
- Satellite and environmental APIs are now publicly accessible at meaningful resolution
- LLMs can translate complex biophysical signals into plain-language financial narratives
- Agricultural credit is a multi-trillion dollar global market with almost no real-time data integration

### 1.6 Core Product Principles

**The Bridge is the Product**
Every feature must require both climate science and financial logic to function. If it only touches one side, it doesn't belong in the MVP.

**Awe First, Explanation Second**
The demo leads with visual impact — map overlays, live recalculation, shifting risk curves. Explanation follows naturally. Never bury the visual.

**Two Audiences, One System**
Loan officers and farmers see the same underlying data through different lenses. The system serves both without requiring two separate builds.

**Real APIs, Reliable Demo**
Integrate real climate data sources where possible. Maintain a fully seeded mock fallback so the demo never fails due to an external API.

**AI Explains, Rules Decide**
The risk scoring engine uses deterministic formulas. Claude translates outcomes into plain language for both panels. No black box decisions.

---

## 2. Users & Personas

### 2.1 Primary User A — Loan Officer (Bank Side)

- Reviews farm loan applications
- Currently relies on credit score, historical yield averages, and regional risk tables
- Has no real-time environmental data at point of decision
- Needs: a risk score they can trust, a clear explanation of why it changed, and audit-ready reasoning

### 2.2 Primary User B — Farmer (Human Side)

- Applying for or managing an agricultural loan
- Understands their land intimately but has no visibility into how banks are pricing their risk
- Needs: transparency into what environmental factors are affecting their terms, and confidence that the system is working in their favor

### 2.3 Demo Persona (Hackathon)

For the demo, both panels are shown to judges. The narrative follows a single farm in a US agricultural region experiencing a simulated climate event, showing how the system responds in real time from both perspectives simultaneously.

### 2.4 Jobs-to-be-Done

- "Show me this farm's real climate risk, not a regional average." (Loan officer)
- "Tell me why my interest rate just changed." (Farmer)
- "What happens to this loan if we get a drought next month?" (Both)
- "Which farms in my portfolio are most exposed to heat stress this season?" (Loan officer)

---

## 3. Product Scope

### 3.1 MUST HAVE (Hackathon MVP)

- Interactive US map with farm region selection (click to select region)
- Real-time climate data ingestion (NOAA API + mock fallback)
- Vegetation health overlay (NDVI — mock or NASA MODIS)
- Soil moisture overlay (mock data, architected as real)
- Yield stress score computation (deterministic formula engine)
- Financial risk translation (yield stress → probability of default → interest rate)
- Climate shock simulator (temperature slider, drought toggle, rainfall anomaly slider)
- Live recalculation of all financial outputs when climate inputs shift
- Dual-panel UI: Loan Officer view + Farmer view (switchable via tab buttons)
- Financial outputs: interest rate, probability of default, insurance premium estimate, repayment schedule impact
- AI narrative layer (Claude via AWS Bedrock): plain-language explanation of why terms changed
- Static underwriting comparison ("old system" vs TerraLend side-by-side)
- AI Underwriting Assistant: Logic layer that evaluates climate/financial data to propose specific interest rate floors and ceilings.
- Downloadable Risk Memo: A professional PDF or text-based summary generated by the assistant, detailing the climate-financial correlation and explicit term suggestions.
- Simulation Lab View: A dedicated UI tab for "Stress Testing" a loan against climate archetypes.
- Scenario Exploration Agent: A "Run Simulations" engine that executes batch tests against predefined climate models and provides a high-level summary report.
- Heuristic Fallback: Hard-coded "Best/Worst" case math to ensure the Simulation Lab remains functional if LLM APIs are latent or down.
- Mock fallback data layer for all external APIs

### 3.2 SHOULD HAVE (Stretch Goals)

- Adaptive loan contract simulation (if drought index crosses threshold → payment schedule flexes)
- Portfolio heat map (loan officer sees all monitored farms colored by risk level)
- Early repayment discount simulation (rainfall surplus → incentive shown)
- Equity analytics layer (flags farms in structurally high-risk climate zones)
- Global region support (expand beyond US)

### 3.3 OUT OF SCOPE

- Real loan origination or execution
- Actual financial advice or regulated outputs
- Full ML model training (use deterministic formula for hackathon)
- Real KYC or identity verification
- Mobile native app
- Multi-user authentication system

### 3.4 Hackathon Success Criteria

- Judge can select a US farm region on the map in under 10 seconds
- Climate overlays render visibly on the map
- Adjusting any climate slider causes financial outputs to update in under 2 seconds
- AI explanation updates dynamically with each change
- Old system vs TerraLend comparison is immediately legible
- Demo runs fully on mock fallback if APIs are unavailable
- Both loan officer and farmer panels are navigable via UI tabs

---

## 4. Core User Flows

### 4.1 Farm Region Selection

1. User lands on TerraLend dashboard
2. Map of US agricultural regions is displayed (choropleth or pin-based)
3. User clicks a region to select it
4. System loads climate data for that region (real API attempt → mock fallback)
5. Climate overlays render on map
6. Default loan profile loads for the region
7. Financial outputs calculate and display

**Failure handling:**
- API unavailable: silent fallback to mock data, no error shown to user
- Region has no data: display nearest available region's data with label

### 4.2 Climate Data Ingestion

1. On region select, backend calls NOAA API for temperature and precipitation data
2. NDVI vegetation index loaded (NASA MODIS or mock)
3. Soil moisture index loaded (mock, architected as real endpoint)
4. All values normalized to 0–100 stress index scale
5. Yield Stress Score computed from weighted formula
6. Financial risk translator maps stress score to financial outputs
7. All values passed to frontend for display

### 4.3 Yield Stress Score Computation

The core formula:

```
yield_stress_score = (
  w1 * heat_stress_index +
  w2 * drought_index +
  w3 * rainfall_anomaly_index +
  w4 * (100 - ndvi_health_score) +
  w5 * soil_moisture_deficit
) / sum(weights)
```

Default weights (tunable):
- Heat stress: 0.30
- Drought index: 0.25
- Rainfall anomaly: 0.20
- Vegetation health (inverted): 0.15
- Soil moisture deficit: 0.10

Output: `yield_stress_score` (0–100, higher = more stressed)

### 4.4 Financial Risk Translation

```
probability_of_default (PD) = base_PD + (yield_stress_score / 100) * stress_multiplier

interest_rate = base_rate + (PD * rate_sensitivity)

insurance_premium = base_premium * (1 + yield_stress_score / 100)

repayment_flexibility_score = 100 - yield_stress_score
```

Default parameters:
- `base_PD`: 0.05 (5%)
- `stress_multiplier`: 0.25
- `base_rate`: 5.5%
- `rate_sensitivity`: 0.08
- `base_premium`: $1,200/season

### 4.5 Climate Shock Simulation

1. User adjusts a climate slider (temperature, drought, rainfall)
2. Frontend sends updated parameters to backend in real time
3. Backend recomputes yield stress score with new inputs
4. Financial outputs recalculate
5. AI narrative regenerates (Claude call with updated context)
6. All panels update simultaneously within 2 seconds
7. Delta indicators show change vs baseline ("↑ +0.9% rate")

### 4.6 AI Narrative Generation (Claude via Bedrock)

Triggered on: initial load, any slider change, panel switch.

Claude receives:
- Current climate inputs (all indices)
- Yield stress score
- All financial outputs
- Active panel context (loan officer or farmer)
- Delta from baseline

Claude generates:
- 2–3 sentence plain-language explanation of current risk
- 1 sentence on the dominant contributing factor
- 1 sentence on what would need to change to improve terms
- Loan officer mode: clinical, data-referenced tone
- Farmer mode: empathetic, plain-language, outcome-focused tone

**Fallback:** pre-written template strings if Claude call fails.

### 4.7 Dual Panel Navigation

1. Dashboard loads in Loan Officer view by default
2. Three tab buttons visible at top: **Loan Officer | Farmer | Climate Scientist**
3. Clicking a tab animates panel transition
4. All underlying data remains the same — only presentation layer changes
5. Each panel has its own AI narrative tone (same Claude call, different system prompt context)

### 4.8 AI Underwriting Assistant Flow
1. Trigger: Loan Officer clicks "Generate Underwriting Proposal" in the main panel.
2. Analysis: The agent reads the current yield_stress_score and financial_outputs.
3. Suggestion: The agent presents explicit Interest Rate Floor and Ceiling recommendations (e.g., "Floor: 5.8% | Ceiling: 8.2%").
4. Outcome: User clicks "Export Risk Memo," generating a formal write-up for the credit committee that justifies these bounds based on specific climate volatility.

### 4.9 Autonomous Scenario Exploration (Simulation Lab)
1. Navigation: User enters the Simulation Lab tab.
2. Execution: User clicks "Run Climate Stress Test".
3. Backend Processing: The system silently runs the simulation engine across four Climate Archetypes:
        The Dust Bowl Echo (Severe Drought/High Temp)
        The Deluge (Flash Flood/Rainfall Anomaly)
        The Late Frost (Temperature Snap)
        The Baseline (Seasonal Norms)
4. Reporting: The UI displays a "Climate Resilience Report" showing the Spread (Best Case vs. Worst Case Interest Rates) and a "Most Likely" outcome summary generated by the agent.

**Panel content per view:**

**Loan Officer Panel:**
- Risk score with confidence band
- Probability of default
- Recommended interest rate
- Insurance premium estimate
- Repayment schedule impact
- Portfolio comparison (if stretch goal reached)
- Clinical AI narrative

**Farmer Panel:**
- "Your loan terms today" summary card
- Plain-language explanation of what's affecting their rate
- What they could do to improve their terms (if anything)
- Seasonal outlook (next 30 days)
- Empathetic AI narrative

**Climate Scientist Panel:**
- Raw index values for all climate inputs
- Yield stress formula breakdown (which factors contributing most)
- NDVI and soil moisture charts over time
- Technical AI narrative with data citations

---

## 5. Feature Specifications

### 5.1 Interactive US Map

- Library: Leaflet.js or Mapbox GL (free tier)
- US agricultural regions pre-defined (approx 20–30 clickable zones)
- Choropleth coloring based on current yield stress score
- Click → triggers full data load for that region
- Overlay toggles: NDVI vegetation, soil moisture, rainfall anomaly, temperature

### 5.2 Climate Shock Simulator

**Sliders:**
- Temperature anomaly: -3°C to +5°C above seasonal norm
- Drought intensity: 0 (none) to 100 (severe)
- Rainfall anomaly: -80% to +80% of seasonal average

**Toggle events:**
- Sudden drought shock (15-day heatwave simulation)
- Flash flood event
- Early frost event

All inputs feed directly into yield stress formula in real time.

### 5.3 Financial Output Display

All outputs update live. Each shows:
- Current value (large, prominent)
- Delta from baseline (colored indicator: red = worse, green = better)
- Sparkline showing value over simulated time

Outputs:
- Interest rate (%)
- Probability of default (%)
- Estimated insurance premium ($/season)
- Repayment flexibility score (0–100)
- Repayment schedule (months, with flex indicator)

### 5.4 Old System vs TerraLend Comparison

Static panel visible on load:

```
OLD SYSTEM                    TERRALEND
─────────────────────────────────────────
Rate: 7.2%                    Rate: 6.4%
Based on: regional average    Based on: live climate data
Updated: annually             Updated: continuously
Risk model: historical yield  Risk model: microclimate stress
Farmer visibility: none       Farmer visibility: full
```

This framing is the "awe" moment — judges immediately see what's different.

### 5.5 AI Narrative Layer

- Powered by Claude 3.5 Sonnet via AWS Bedrock
- Separate system prompts per panel (loan officer, farmer, climate scientist)
- Streaming response for perceived speed
- Max 4 sentences per narrative
- Fallback template strings for API failure

### 5.6 Mock Data Fallback

All external API calls wrapped in try/except with fallback:
- NOAA temperature/precipitation → pre-seeded JSON per region
- NDVI → static realistic values per region and season
- Soil moisture → static realistic values

Mock data architected identically to real API response shapes — swapping real for mock requires zero code changes.

---

## 5.7 Core UX Decisions (Hackathon Lock)

These decisions are locked for the hackathon build to prioritize simplicity, reliability, and demo stability over realism.

### 5.7.1 Region Selection

**Decision:** Use simple clickable markers instead of polygon GeoJSON regions.

**Implementation**
- 20–30 predefined agricultural regions represented as markers.
- Marker color reflects current yield stress score.
- Clicking a marker triggers full region data load.

**Rationale**
- Faster implementation.
- Avoids GeoJSON parsing/rendering complexity.
- Reduces performance risk during demo.

### 5.7.2 Climate Overlays

**Decision:** Use simplified color tint layers instead of true raster/heat overlays.

**Implementation**
- Region marker color and optional translucent circle indicate stress intensity.
- Overlay toggles modify color coding only.

**Rationale**
- Eliminates heavy geospatial rendering.
- Guarantees smooth performance on demo hardware.

### 5.7.3 Climate Slider Update Behavior

**Decision:** Sliders trigger recalculation only on release (not continuously while dragging).

**Implementation**
- Slider moves locally in UI while dragging.
- Backend simulation call fires on mouse/touch release.
- One recomputation per interaction.

**Rationale**
- Prevents excessive backend and AI calls.
- Ensures deterministic latency.

### 5.7.4 AI Narrative Refresh Strategy

**Decision:** Cache narratives and reuse on panel switch.

**Behavior**
- Narrative regenerates only when climate inputs change.
- Panel switching reuses cached narrative for that panel when available.
- No new Claude call on tab switch unless simulation changed.

**Rationale**
- Instant tab switching.
- Lower latency and cost.
- More reliable demo.

### 5.7.5 Baseline Comparison Behavior

**Decision:** Old-system baseline remains fixed and static.

**Behavior**
- Old system values never change during simulation.
- TerraLend values update dynamically.

**Rationale**
- Clear storytelling.
- Reinforces static vs adaptive comparison.

### 5.7.6 Additional Hackathon Simplifications

- Claude calls are debounced; only one narrative request active at a time.
- If a new simulation starts, the previous narrative request is cancelled.
- Financial outputs update immediately; narrative updates asynchronously.
- No polygon clipping, raster climate layers, or geographic interpolation.
- Climate values are region-level only.

---

## 6. Technical Architecture

### 6.1 Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **AI Layer:** Claude 3.5 Sonnet via AWS Bedrock (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
- **Map:** Leaflet.js
- **Database:** SQLite (hackathon) — stores region profiles, mock data, loan profiles
- **Deployment:** Local / ngrok for demo

### 6.2 Component Overview

- **React Frontend** — map, panels, sliders, tab navigation, output displays
- **FastAPI Backend** — orchestrates all data flows, exposes REST endpoints
- **Climate Ingestion Service** — calls NOAA + NDVI APIs, normalizes inputs, falls back to mock
- **Yield Stress Engine** — deterministic formula, takes normalized climate inputs, outputs stress score
- **Financial Risk Translator** — maps stress score to all financial outputs
- **AI Narrative Service** — constructs Claude prompt with full context, returns panel-specific narrative
- **Mock Data Layer** — pre-seeded realistic data for all regions, all climate variables
- **Region Config Store** — SQLite table of US agricultural regions with coordinates and base loan profiles

### 6.3 API Endpoints

```
GET  /regions                          → list of all selectable US regions
GET  /region/{id}/climate              → current climate data for region
GET  /region/{id}/stress               → yield stress score
GET  /region/{id}/financial            → all financial outputs
POST /simulate                         → recalculate with custom climate inputs
GET  /region/{id}/narrative?panel=X    → Claude narrative for panel context
GET  /region/{id}/comparison           → old system vs TerraLend comparison data
```

### 6.4 Data Flow

```
User selects region
       ↓
Climate Ingestion Service (NOAA + NDVI → mock fallback)
       ↓
Normalize all inputs → 0–100 index scale
       ↓
Yield Stress Engine → stress_score (0–100)
       ↓
Financial Risk Translator → {interest_rate, PD, premium, repayment}
       ↓
AI Narrative Service → Claude prompt → narrative string
       ↓
All outputs → React frontend → live display
```

### 6.5 Climate Simulation Data Flow

```
User moves slider
       ↓
POST /simulate {temperature_delta, drought_index, rainfall_anomaly}
       ↓
Yield Stress Engine recalculates with new inputs
       ↓
Financial outputs recalculate
       ↓
Claude narrative regenerates with delta context
       ↓
Frontend updates all panels simultaneously
```

### 6.6 Security & Infra

- AWS credentials via environment variables (.env)
- No PII stored — demo uses fictional farm profiles
- SQLite for hackathon; architected for DynamoDB migration
- All secrets in .env, never committed to repo

---

## 7. Data Model

### Region
| Field | Type | Notes |
|---|---|---|
| region_id | string | e.g. "central-valley-ca" |
| name | string | Display name |
| lat | float | Center latitude |
| lng | float | Center longitude |
| primary_crop | string | e.g. "wheat", "corn" |
| base_loan_rate | float | Starting interest rate |
| base_pd | float | Base probability of default |
| base_premium | float | Base insurance premium |

### ClimateSnapshot
| Field | Type | Notes |
|---|---|---|
| snapshot_id | string | |
| region_id | string | FK → Region |
| temperature_anomaly | float | °C above/below seasonal norm |
| drought_index | float | 0–100 |
| rainfall_anomaly | float | % above/below seasonal avg |
| ndvi_score | float | 0–100 vegetation health |
| soil_moisture | float | 0–100 |
| yield_stress_score | float | Computed output |
| timestamp | timestamp | |

### FinancialOutput
| Field | Type | Notes |
|---|---|---|
| output_id | string | |
| region_id | string | FK → Region |
| snapshot_id | string | FK → ClimateSnapshot |
| interest_rate | float | % |
| probability_of_default | float | 0–1 |
| insurance_premium | float | $/season |
| repayment_flexibility | float | 0–100 score |
| baseline_rate | float | Old system rate for comparison |
| timestamp | timestamp | |

### SimulationRun
| Field | Type | Notes |
|---|---|---|
| run_id | string | |
| region_id | string | FK → Region |
| input_overrides | JSON | Custom climate inputs |
| stress_score | float | Result |
| financial_outputs | JSON | All computed outputs |
| narrative | string | Claude response |
| panel_context | string | loan_officer / farmer / scientist |
| created_at | timestamp | |

---

## 8. AI / Agent Design

### 8.1 Claude's Role

Claude does not make decisions. The yield stress formula and financial translator are fully deterministic. Claude's job is to make the outputs legible, human, and compelling for each audience.

### 8.2 Loan Officer System Prompt

```
You are a financial risk analyst assistant embedded in an agricultural lending platform.
You receive real-time climate data and computed risk metrics for a farm region.
Your job is to explain the current risk assessment in 3–4 sentences.
Be clinical, precise, and data-referenced.
Always cite the dominant risk factor.
Always note what would need to change for the risk profile to improve.
Never use the word "recommend" — you are providing analysis, not advice.
```

### 8.3 Farmer System Prompt

```
You are a plain-language assistant helping a farmer understand how current
environmental conditions are affecting their loan terms.
Explain in simple, empathetic language (3–4 sentences max).
Focus on outcomes, not technical indices.
If conditions are worsening, be honest but constructive.
If conditions are improving, be encouraging.
Never use jargon. Never mention probability or statistical terms.
```

### 8.4 Climate Scientist System Prompt

```
You are a technical climate analyst providing a breakdown of current
microclimate stress signals for an agricultural region.
Include specific index values and their relative contribution to the overall stress score.
Reference the dominant environmental driver.
Use precise scientific language appropriate for a technical audience.
Keep response to 3–4 sentences.
```

### 8.5 Prompt Context Payload

Each Claude call includes:
```json
{
  "region": "Central Valley, CA",
  "primary_crop": "almonds",
  "climate_inputs": {
    "temperature_anomaly": "+2.3°C",
    "drought_index": 67,
    "rainfall_anomaly": "-34%",
    "ndvi_score": 48,
    "soil_moisture": 31
  },
  "yield_stress_score": 72,
  "financial_outputs": {
    "interest_rate": "7.8%",
    "probability_of_default": "18%",
    "insurance_premium": "$1,890/season",
    "repayment_flexibility": 28
  },
  "baseline_comparison": {
    "old_rate": "7.2%",
    "delta": "+0.6%"
  },
  "delta_from_last": {
    "stress_score_change": "+12",
    "rate_change": "+0.6%"
  },
  "panel_context": "loan_officer"
}
```

### 8.6 Fallback Templates

If Claude call fails:

**Loan Officer:** "Current yield stress score of {score}/100 is driven primarily by {top_factor}. Probability of default has shifted to {pd}%, adjusting the recommended rate to {rate}%. Conditions would need to stabilize for {improvement_condition} to see rate improvement."

**Farmer:** "Right now, {top_factor_plain} is the main thing affecting your loan terms. Your current rate is {rate}. If {improvement_condition_plain}, your terms could improve."

**Climate Scientist:** "Dominant stress driver: {top_factor} (contributing {pct}% of composite score). NDVI at {ndvi}, soil moisture at {soil_moisture}. Composite yield stress: {score}/100."

### 8.7
Role: To act as a "Time Traveler" for the loan, exploring potential futures based on historical and predictive climate archetypes.

System Prompt:

You are a Climate Risk Strategist. Analyze the results of multiple batch simulations.
Summarize the 'Spread' between the best and worst-case interest rates.
Identify which archetype (e.g., Flash Flood vs. Heatwave) poses the greatest existential threat to this specific loan's repayment flexibility.
Keep the summary high-level and focused on the 'Most Likely' financial outcome.

### 8.8 Underwriting Assistant System Prompt (Updated)
You are a Credit Risk Agent. Your goal is to provide explicit boundaries for a loan's interest rate.
Based on the provided yield stress, suggest a Floor (minimum rate to ensure bank viability) and a Ceiling (maximum rate before default risk becomes too high).
Your output will be used to generate a formal Risk Memo. Be precise, avoid jargon, and focus on the 'Climate-to-Credit' transmission mechanism.
---

## 9. Engineering Implementation Plan

### Phase 0 — Setup (2 hours)
- Repo initialization, FastAPI + React scaffold
- .env setup (AWS credentials, API keys)
- SQLite schema creation and migration
- Seed mock data for all US regions
- NOAA API account + key (free tier)

### Phase 1 — Climate Engine (3 hours)
- NOAA API integration (temperature, precipitation)
- NDVI mock data layer (architected as real endpoint)
- Soil moisture mock data layer
- Normalization pipeline (raw API values → 0–100 indices)
- Yield stress formula implementation and unit tests
- `/region/{id}/climate` and `/region/{id}/stress` endpoints live

### Phase 2 — Financial Translator (2 hours)
- Financial risk translation formulas implemented
- All financial output fields computed
- `/region/{id}/financial` endpoint live
- Old system baseline values seeded per region
- `/region/{id}/comparison` endpoint live

### Phase 3 — Frontend Core (4 hours)
- React app scaffold with Vite
- Leaflet.js map with US agricultural regions
- Region click → API call → data load
- Climate overlay toggles on map (NDVI, soil moisture, temperature)
- Financial output display panel (all fields, delta indicators)
- Old system vs TerraLend comparison panel

### Phase 4 — Climate Shock Simulator (2 hours)
- Slider components (temperature, drought, rainfall)
- Toggle buttons (drought shock, frost event, flood event)
- `POST /simulate` endpoint
- Real-time recalculation on slider change (debounced 300ms)
- Delta indicators update with each change

### Phase 5 — AI Narrative Layer (2 hours)
- Claude integration via AWS Bedrock
- Three system prompts (loan officer, farmer, climate scientist)
- `/region/{id}/narrative` endpoint with panel context
- Streaming response to frontend
- Fallback template strings implemented

### Phase 6 — Dual Panel UI + Polish (3 hours)
- Three-tab navigation (Loan Officer | Farmer | Climate Scientist)
- Panel-specific layout and tone per view
- Animated tab transitions
- Full responsive layout
- Demo seed data verified for all regions
- End-to-end flow tested

### Phase 7 — Demo Hardening (2 hours)
- Mock fallback tested and verified for all API failure scenarios
- Deterministic replay mode for demo (fixed region + fixed inputs)
- Seed data double-checked for realistic values
- Demo script written and rehearsed

---

## 10. Engineering Task Breakdown

**Backend**
- [ ] FastAPI project scaffold
- [ ] SQLite schema + migrations
- [ ] Region seed data (20+ US agricultural regions)
- [ ] NOAA API integration
- [ ] Mock data layer (all climate variables)
- [ ] Normalization pipeline
- [ ] Yield stress formula engine
- [ ] Financial risk translator
- [ ] Claude narrative service (3 system prompts)
- [ ] All REST endpoints
- [ ] POST /simulate endpoint
- [ ] Mock fallback for all endpoints
- [ ] Archetype Engine: Create 4 preset climate input JSONs (Dust Bowl, Deluge, etc.).
- [ ] Batch Simulation Endpoint: POST /simulate/batch to run all 4 archetypes and return the data array.
- [ ] Memo Generation Service: Logic to format LLM output into a downloadable text/PDF risk memo.
- [ ] Heuristic Backup: Simple min/max calculation script for the Simulation Lab.

**Frontend**
- [ ] React + Vite scaffold
- [ ] Leaflet.js map with US regions
- [ ] Region click handler
- [ ] Climate overlay toggles
- [ ] Financial output panel (all fields + deltas)
- [ ] Old system vs TerraLend comparison component
- [ ] Climate shock sliders + toggles
- [ ] Three-tab panel navigation
- [ ] AI narrative display component (streaming)
- [ ] Delta indicator components (red/green)
- [ ] Loading states for all async calls
- [ ] Simulation Lab Tab: New view containing the "Run" button and a summary dashboard.
- [ ] Archetype Progress UI: A "Processing..." state that hides the backend loops.
- [ ] Proposal Component: Display for the suggested Rate Floor/Ceiling.
- [ ] Download Trigger: Button to trigger the Risk Memo download.

**Data**
- [ ] Mock climate data seeded for all regions (realistic values)
- [ ] Base loan profiles per region
- [ ] Seasonal baseline values per region
- [ ] Shock event presets (drought, frost, flood)

**Demo Tooling**
- [ ] Deterministic demo mode (fixed inputs, guaranteed outputs)
- [ ] Demo script document
- [ ] ngrok or equivalent for live demo URL

---

## 11. Demo Strategy

### 11.1 The Opening (Awe — first 20 seconds)

Show the comparison panel first. No explanation — just let judges read:

```
OLD SYSTEM          →       TERRALEND
Rate: 7.2%                  Rate: 6.4%
Updated: annually            Updated: continuously  
Based on: region average     Based on: live microclimate data
Farmer visibility: none      Farmer visibility: full
```

Then say: *"This is what changes when climate science and finance finally talk to each other."*

### 11.2 The Demo Flow

1. Map loads — US agricultural regions visible, colored by current stress level
2. Click **Central Valley, CA** — overlays render (NDVI, soil moisture, temperature)
3. Financial outputs populate on the right panel
4. Show **Loan Officer view** — clinical risk breakdown, Claude narrative
5. Switch to **Farmer view** — same data, human language, "your rate is 6.4% because..."
6. Switch to **Climate Scientist view** — raw index values, formula breakdown
7. Move the **temperature slider** +3°C — watch interest rate climb in real time
8. Trigger **drought shock toggle** — NDVI drops, stress score spikes, rate jumps to 8.1%
9. Claude narrative updates: *"Heat stress is now the dominant risk driver..."*
10. Return sliders to baseline — show rate recovering
11. Close with equity framing: *"The farmers who need fair terms the most are the ones most exposed to climate. TerraLend makes the invisible visible."*

### 11.3 The Wow Moment

Drought toggle fires. Map darkens. Interest rate visibly jumps. Claude explains why in plain English. The loan officer sees risk. The farmer sees impact. Same event, two perspectives, one system.

### 11.4 Fallback Demo

- All API calls pre-cached with realistic mock data
- Demo mode flag in .env forces mock data regardless of API status
- Zero dependency on live external APIs during presentation

### 11.5 The "Stress Test" Moment (The New Closer)
- After showing the manual sliders, navigate to the Simulation Lab.
- Click "Run Climate Stress Test".
- Wait 2 seconds (silent backend processing).
- The "Climate Resilience Report" appears.
- The Narrator says: "Instead of guessing, our agent just ran this farm through 50 years of simulated volatility. In a 'Dust Bowl' scenario, the rate peaks at 9.2%, but our suggested ceiling of 8.5% keeps the farmer solvent while protecting the bank."
- Click "Download Risk Memo" to show a professional, audit-ready document.

---

## 12. Metrics & Validation

### 12.1 Demo Metrics
- Time to first meaningful output after region select (target: < 2 seconds)
- Slider recalculation latency (target: < 2 seconds including Claude)
- Claude narrative generation time (target: < 3 seconds with streaming)

### 12.2 Model Validation
- Yield stress scores produce realistic financial output ranges
- Interest rate delta between best and worst case is meaningful (target: 2–4% spread)
- Probability of default range feels realistic (5%–35%)

### 12.3 Demo Reliability
- End-to-end flow completable with zero API calls (full mock mode)
- All three panel views render without errors
- Shock simulation produces visible, legible change in all outputs

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| NOAA API rate limits or downtime | Full mock fallback layer, demo mode flag |
| Claude response too slow for live demo | Streaming + pre-cached narratives for demo regions |
| Map library complexity delays frontend | Use Leaflet.js (simpler) over Mapbox, pre-built region GeoJSON |
| Financial formula produces unrealistic outputs | Unit test all edge cases in Phase 1, clamp output ranges |
| Claude narrative doesn't update fast enough on slider change | Debounce slider at 300ms, show loading state, cache last valid response |
| Too ambitious for 24 hours | Phases 0–5 are MVP. Phase 6–7 are polish. Ship Phase 5 and demo is complete. |

---

## 14. Future Extensions (Reach Goals)

### SHOULD HAVE (if time permits)

**Adaptive Loan Contracts**
Dynamic contract terms that flex based on real-time climate triggers:
- If drought index crosses 70 → payment schedule extends automatically
- If rainfall surplus detected → early repayment discount offered
- Visual contract timeline that shifts as climate inputs change

**Portfolio Heat Map**
Loan officer sees all monitored farm regions simultaneously, colored by current stress level. Identifies which loans in the portfolio are most exposed before problems occur.

**Equity Analytics Layer**
Flags farm regions that are structurally disadvantaged by climate — high stress scores despite good farming practices. Proposes pooled climate risk fund adjustments to reduce systemic bias in underwriting.

**Global Region Support**
Expand map beyond US to support major global agricultural regions — Punjab (India), São Paulo (Brazil), Sub-Saharan Africa. Same architecture, new region seed data.

### OUT OF SCOPE (post-hackathon roadmap)

- Real loan origination or execution
- Actual ML model training on historical yield data
- Integration with real bank underwriting systems
- Regulatory compliance stack
- Mobile native app
- Multi-tenant authentication

---

## 15. Open Questions

**Technical**
- Which GeoJSON source for US agricultural region boundaries? (USDA provides free shapefiles)
- Should NDVI use NASA MODIS API or purely mock for reliability?
- Debounce interval for slider → API call: 300ms or 500ms?
- Stream Claude response to frontend or wait for full completion?

**Product**
- Should the farmer panel show the raw stress score number or hide it and only show outcomes?
- Does the Climate Scientist panel need chart visualizations or is tabular data sufficient for hackathon?
- Should shock event presets be named after real historical events (e.g. "2012 Midwest Drought") for emotional impact?

**Demo**
- Which US region should be the default demo region? (Recommendation: Central Valley, CA — most recognizable)
- Should the demo start in a "normal" climate state and deteriorate, or start in stress and recover?
- How long is the demo slot — 2 minutes or 5 minutes?
