# Developer 3: AI Narrative Layer + Simulation Lab

**Scope**: Claude integration via AWS Bedrock, narrative generation for all three panels, streaming responses, fallback templates, underwriting assistant, simulation lab (batch stress tests), risk memo generation.
**Independence**: All AI services are standalone Python modules with their own test harness. Uses hardcoded mock climate/financial inputs for testing — zero dependency on backend server or frontend. Exposes functions and FastAPI routes that get wired in during integration.
**Convention**: Every subtask ends with tests covering happy path + edge cases + API failure modes.

---

## Task 1: AWS Bedrock Client Setup

### 1.1 Bedrock client wrapper
- Create `backend/services/ai/bedrock_client.py`:
  - `BedrockClient` class that wraps `boto3` Bedrock Runtime client
  - Constructor takes `region`, `access_key`, `secret_key` from config (or env vars)
  - `async invoke(system_prompt: str, user_message: str, max_tokens: int = 500) -> str` — synchronous call, returns full response text
  - `async invoke_stream(system_prompt: str, user_message: str, max_tokens: int = 500) -> AsyncGenerator[str, None]` — streaming, yields chunks
  - Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - Timeout: 15 seconds
  - Error handling: catch all boto3/Bedrock exceptions, return `None` on failure
- Create `backend/services/ai/__init__.py`

**Tests after 1.1:**
- [ ] `invoke()` returns string when given valid prompts (mock boto3 response)
- [ ] `invoke()` returns `None` on timeout (mock timeout exception)
- [ ] `invoke()` returns `None` on auth failure (mock credentials exception)
- [ ] `invoke()` returns `None` on throttling (mock ThrottlingException)
- [ ] `invoke_stream()` yields chunks (mock streaming response)
- [ ] `invoke_stream()` handles mid-stream failure gracefully
- [ ] Max tokens parameter passed correctly to API
- [ ] System prompt and user message formatted correctly in Bedrock message format

---

## Task 2: AI Narrative Service

### 2.1 System prompts
- Create `backend/services/ai/prompts.py`:
  - `LOAN_OFFICER_SYSTEM_PROMPT` — clinical, data-referenced tone (from PRD Section 8.2)
  - `FARMER_SYSTEM_PROMPT` — empathetic, plain-language (from PRD Section 8.3)
  - `CLIMATE_SCIENTIST_SYSTEM_PROMPT` — technical with data citations (from PRD Section 8.4)
  - `UNDERWRITING_ASSISTANT_PROMPT` — rate floor/ceiling suggestions (from PRD Section 8.8)
  - `SCENARIO_STRATEGIST_PROMPT` — batch simulation summary (from PRD Section 8.7)

**Tests after 2.1:**
- [ ] All five prompts are non-empty strings
- [ ] Loan officer prompt contains "clinical" or "precise" or "data-referenced"
- [ ] Farmer prompt contains "plain-language" or "empathetic" or "simple"
- [ ] Scientist prompt contains "technical" or "scientific" or "index values"
- [ ] No prompt exceeds 1000 characters (keep them focused)

### 2.2 Narrative context builder
- Create `backend/services/ai/narrative.py`:
  - `build_narrative_context(region_name, primary_crop, climate_inputs, yield_stress_score, financial_outputs, baseline_comparison, delta_from_last, panel_context) -> str`
  - Formats all data into the user message payload that Claude receives (PRD Section 8.5)
  - Returns a clean string with all values formatted for clarity
  - `get_dominant_factor(climate_inputs, weights) -> tuple[str, float]` — returns the factor contributing most to stress

**Tests after 2.2:**
- [ ] Context string includes region name and crop
- [ ] Context string includes all 5 climate inputs
- [ ] Context string includes stress score and all financial outputs
- [ ] Context string includes deltas from baseline
- [ ] `get_dominant_factor()` correctly identifies the highest-weighted contributor
- [ ] Handles edge case: all factors equal → returns first one (deterministic)
- [ ] Handles edge case: all zeros → returns meaningful result

### 2.3 Narrative generation service
- Create `backend/services/ai/narrative_service.py`:
  - `NarrativeService` class:
    - Constructor takes `BedrockClient`
    - `async generate(context_payload: dict, panel: str) -> str` — builds prompt, calls Claude, returns narrative
    - `async generate_stream(context_payload: dict, panel: str) -> AsyncGenerator[str, None]` — streaming version
    - On any Claude failure → falls back to template-based narrative
  - Cache: stores last narrative per (region_id, panel) key. Reuses on panel switch when climate inputs haven't changed.
  - Debounce: if called while a previous call is in-flight, cancels previous

**Tests after 2.3:**
- [ ] `generate()` returns narrative string for loan_officer panel (mock Bedrock response)
- [ ] `generate()` returns narrative string for farmer panel
- [ ] `generate()` returns narrative string for scientist panel
- [ ] On Bedrock failure, returns fallback template string (not None/empty)
- [ ] Fallback template includes actual data values (not just static text)
- [ ] Cache returns stored narrative when called with same inputs
- [ ] Cache invalidated when climate inputs change
- [ ] Streaming version yields chunks progressively
- [ ] Debounce: second call cancels first (only latest response returned)

### 2.4 Fallback template engine
- Create `backend/services/ai/fallback_templates.py`:
  - `generate_fallback(panel: str, context: dict) -> str` — returns template-based narrative
  - Templates from PRD Section 8.6:
    - **Loan Officer:** "Current yield stress score of {score}/100 is driven primarily by {top_factor}. Probability of default has shifted to {pd}%, adjusting the recommended rate to {rate}%. Conditions would need to stabilize for {improvement_condition} to see rate improvement."
    - **Farmer:** "Right now, {top_factor_plain} is the main thing affecting your loan terms. Your current rate is {rate}. If {improvement_condition_plain}, your terms could improve."
    - **Scientist:** "Dominant stress driver: {top_factor} (contributing {pct}% of composite score). NDVI at {ndvi}, soil moisture at {soil_moisture}. Composite yield stress: {score}/100."
  - Template fills with actual data values
  - `top_factor` maps to human-readable name (e.g., "heat_stress" → "elevated temperatures" for farmer, "heat stress index" for scientist)

**Tests after 2.4:**
- [ ] Loan officer fallback includes stress score, top factor, PD, rate
- [ ] Farmer fallback uses plain language (no jargon)
- [ ] Scientist fallback includes raw index values
- [ ] All templates produce grammatically correct English with realistic data
- [ ] Factor name mapping works for all 5 factors in all 3 panel modes
- [ ] Template handles edge: zero stress → "conditions are favorable" type message
- [ ] Template handles edge: max stress → appropriately alarming language

---

## Task 3: AI Narrative API Endpoint

### 3.1 Narrative endpoint
- Create `backend/routes/narrative.py`:
  - `GET /region/{region_id}/narrative?panel=loan_officer` — returns JSON `{"narrative": "...", "source": "claude|fallback"}`
  - `GET /region/{region_id}/narrative/stream?panel=loan_officer` — SSE streaming endpoint
  - Accepts `panel` query param: `loan_officer`, `farmer`, `scientist`
  - Loads climate + financial data for region, builds context, calls NarrativeService
  - Returns cached narrative when available (with `"source": "cache"`)

**Tests after 3.1:**
- [ ] Endpoint returns narrative for each panel type
- [ ] Invalid panel value returns 400 error
- [ ] Invalid region_id returns 404
- [ ] Response includes `source` field (claude, fallback, or cache)
- [ ] Streaming endpoint sends SSE events
- [ ] Streaming endpoint closes connection after completion
- [ ] Subsequent call with same inputs returns cached result
- [ ] Call with different region returns fresh narrative

---

## Task 4: Underwriting Assistant

### 4.1 Rate floor/ceiling calculator
- Create `backend/services/ai/underwriting.py`:
  - `calculate_rate_bounds(yield_stress_score, base_rate, financial_outputs) -> dict`:
    - `floor`: minimum rate to ensure bank viability = `base_rate + (yield_stress_score / 100) * 0.5`  (bank can't go below cost of funds)
    - `ceiling`: maximum rate before default risk is too high = `floor + 3.0` (capped so farmer isn't priced out)
    - `recommended`: midpoint weighted toward ceiling as stress increases
    - Clamp floor: 3.0% – 8.0%, ceiling: 5.0% – 12.0%
  - `async generate_underwriting_proposal(context: dict, bedrock_client) -> dict`:
    - Calls Claude with underwriting prompt + context
    - Returns: `{"floor": X, "ceiling": Y, "recommended": Z, "rationale": "...", "source": "claude|heuristic"}`
    - On Claude failure: use heuristic `calculate_rate_bounds()` + static rationale

**Tests after 4.1:**
- [ ] Low stress (10) → tight floor/ceiling spread (e.g., 5.0% / 6.5%)
- [ ] High stress (85) → wide floor/ceiling spread (e.g., 7.0% / 10.0%)
- [ ] Floor is always less than ceiling
- [ ] Floor never below 3.0%, ceiling never above 12.0%
- [ ] Recommended is between floor and ceiling
- [ ] Claude failure → heuristic values returned with `source: "heuristic"`
- [ ] Response includes rationale string (non-empty)

### 4.2 Underwriting endpoint
- Create route `POST /region/{region_id}/underwriting`:
  - Loads climate + financial data
  - Calls `generate_underwriting_proposal()`
  - Returns floor, ceiling, recommended, rationale
- Wire into router

**Tests after 4.2:**
- [ ] Endpoint returns all fields: floor, ceiling, recommended, rationale, source
- [ ] 404 for invalid region_id
- [ ] Different regions produce different rate bounds
- [ ] Endpoint works in demo mode (mock data)

---

## Task 5: Simulation Lab Engine

### 5.1 Climate archetype presets
- Create `backend/services/ai/archetypes.py`:
  - Four preset climate scenarios:
    ```python
    ARCHETYPES = {
      "dust_bowl": {
        "name": "The Dust Bowl Echo",
        "description": "Severe drought with extreme heat",
        "temperature_delta": 4.5,
        "drought_index": 95,
        "rainfall_anomaly": -70
      },
      "deluge": {
        "name": "The Deluge",
        "description": "Flash flooding with rainfall anomaly",
        "temperature_delta": 1.0,
        "drought_index": 5,
        "rainfall_anomaly": 75
      },
      "late_frost": {
        "name": "The Late Frost",
        "description": "Sudden temperature drop during growing season",
        "temperature_delta": -3.0,
        "drought_index": 25,
        "rainfall_anomaly": -15
      },
      "baseline": {
        "name": "The Baseline",
        "description": "Seasonal norms — no anomalies",
        "temperature_delta": 0.0,
        "drought_index": 30,
        "rainfall_anomaly": 0
      }
    }
    ```
  - `get_archetype(name) -> dict`
  - `get_all_archetypes() -> list[dict]`

**Tests after 5.1:**
- [ ] All 4 archetypes defined with required keys
- [ ] `get_archetype("dust_bowl")` returns correct preset
- [ ] `get_archetype("nonexistent")` raises/returns None
- [ ] `get_all_archetypes()` returns list of 4
- [ ] Each archetype has name, description, and all 3 climate override fields
- [ ] Dust bowl is the most extreme (highest stress expected)
- [ ] Baseline is neutral (lowest stress expected)

### 5.2 Batch simulation engine
- Create `backend/services/ai/simulation_lab.py`:
  - `async run_batch_simulation(region_id, base_climate, base_financial, stress_engine_fn, financial_translator_fn) -> dict`:
    - Runs all 4 archetypes through the yield stress + financial translator
    - For each archetype: merge overrides with base climate → compute stress → compute financial
    - Returns:
      ```python
      {
        "region_id": "...",
        "results": [
          {
            "archetype": "dust_bowl",
            "name": "The Dust Bowl Echo",
            "stress_score": 87.3,
            "interest_rate": 9.2,
            "probability_of_default": 0.27,
            "insurance_premium": 2244,
            "repayment_flexibility": 12.7
          },
          # ... 3 more
        ],
        "spread": {
          "best_rate": 5.8,
          "worst_rate": 9.2,
          "spread": 3.4,
          "best_archetype": "baseline",
          "worst_archetype": "dust_bowl"
        },
        "most_likely": { ... }  # average of all 4 results
      }
      ```
  - Does NOT require Claude — pure deterministic computation
  - `most_likely` is the mean of all 4 results

**Tests after 5.2:**
- [ ] Returns results for all 4 archetypes
- [ ] Dust bowl produces highest stress score
- [ ] Baseline produces lowest stress score
- [ ] Spread is correctly computed (worst rate - best rate)
- [ ] Best/worst archetype names are correct
- [ ] Most likely values are the mean of all 4
- [ ] Different regions produce different batch results (different base values)
- [ ] All financial outputs present for each archetype result
- [ ] Results are ordered by severity (worst first) or by archetype name (consistent)

### 5.3 Batch simulation summary (AI-powered)
- Add to `simulation_lab.py`:
  - `async generate_resilience_report(batch_results: dict, bedrock_client) -> str`:
    - Calls Claude with scenario strategist prompt + batch results
    - Claude summarizes: spread, greatest threat, most likely outcome
    - On failure: generate heuristic summary from the data directly
  - Heuristic fallback:
    - "Climate resilience analysis for {region}: Interest rates range from {best_rate}% (baseline) to {worst_rate}% ({worst_archetype}). The {worst_archetype} scenario poses the greatest risk to repayment flexibility (score: {worst_flexibility}/100). Most likely outcome: {avg_rate}% interest rate."

**Tests after 5.3:**
- [ ] Claude-powered summary returned when Bedrock succeeds (mock)
- [ ] Heuristic summary returned when Bedrock fails
- [ ] Heuristic summary includes actual data values (not placeholders)
- [ ] Summary mentions the worst archetype by name
- [ ] Summary includes rate spread
- [ ] Summary handles edge: all archetypes produce similar results → "resilient" message

### 5.4 Batch simulation endpoint
- Create `backend/routes/simulation_lab.py`:
  - `POST /simulate/batch`:
    - Request: `{"region_id": "central-valley-ca"}`
    - Response: full batch results + spread + AI summary
  - `GET /archetypes` — returns list of available climate archetypes

**Tests after 5.4:**
- [ ] `POST /simulate/batch` returns results for all 4 archetypes
- [ ] Response includes spread and most_likely
- [ ] Response includes AI summary string
- [ ] 404 for invalid region_id
- [ ] `GET /archetypes` returns 4 archetype definitions
- [ ] Endpoint responds within 10 seconds (even with Claude call)

---

## Task 6: Risk Memo Generation

### 6.1 Memo content generator
- Create `backend/services/ai/memo_generator.py`:
  - `async generate_risk_memo(region_data, climate_data, financial_data, batch_results, underwriting_proposal, bedrock_client) -> str`:
    - Calls Claude to generate a professional risk memo combining all data
    - Structured sections: Executive Summary, Climate Assessment, Financial Impact, Rate Recommendation, Risk Factors, Conclusion
    - On failure: generates structured memo from template
  - `generate_template_memo(region_data, climate_data, financial_data, batch_results, underwriting_proposal) -> str`:
    - Template-based memo (no AI needed)
    - Same sections, filled with actual data

**Tests after 6.1:**
- [ ] AI memo returned when Bedrock succeeds (mock)
- [ ] Template memo returned when Bedrock fails
- [ ] Memo includes region name and crop type
- [ ] Memo includes climate assessment with all 5 indices
- [ ] Memo includes financial outputs
- [ ] Memo includes rate floor/ceiling recommendation
- [ ] Memo includes batch simulation spread
- [ ] Template memo is well-formatted text (readable)
- [ ] Memo length is reasonable (500–2000 words)

### 6.2 Memo download endpoint
- Create route `POST /region/{region_id}/memo`:
  - Generates full risk memo
  - Returns as plain text with `Content-Type: text/plain` (or `application/pdf` if stretch)
  - Includes timestamp and region identifier in header

**Tests after 6.2:**
- [ ] Endpoint returns text content
- [ ] Content-Type is text/plain
- [ ] Memo includes current timestamp
- [ ] 404 for invalid region_id
- [ ] Memo content is non-empty and structured

---

## Task 7: Heuristic Fallbacks for Full Offline Mode

### 7.1 Complete fallback chain verification
- Verify all AI-powered features have working heuristic fallbacks:
  - [ ] Narrative generation → template fallback
  - [ ] Underwriting proposal → `calculate_rate_bounds()` heuristic
  - [ ] Batch simulation summary → heuristic summary string
  - [ ] Risk memo → `generate_template_memo()`
- Create `backend/services/ai/test_offline_mode.py`:
  - Integration test that mocks ALL Bedrock calls to fail
  - Exercises every AI endpoint
  - Verifies every response contains meaningful data (not empty/None)

**Tests after 7.1:**
- [ ] All endpoints return valid data with Bedrock completely mocked to fail
- [ ] No endpoint returns 500 or empty response
- [ ] All fallback responses include actual data values
- [ ] Source field in responses correctly shows "fallback" or "heuristic"
- [ ] User experience is degraded but functional without Claude

---

## Summary Checklist

- [ ] Task 1: Bedrock Client Wrapper
- [ ] Task 2: AI Narrative Service (prompts, context, generation, fallbacks)
- [ ] Task 3: Narrative API Endpoint (JSON + SSE streaming)
- [ ] Task 4: Underwriting Assistant (rate bounds + endpoint)
- [ ] Task 5: Simulation Lab (archetypes, batch engine, AI summary, endpoint)
- [ ] Task 6: Risk Memo Generation (AI + template, download endpoint)
- [ ] Task 7: Full Offline Mode Verification
