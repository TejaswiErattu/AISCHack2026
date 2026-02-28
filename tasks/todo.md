# RemitAgent — Task Tracker

## Phase 0 — Project Setup (Day 1 morning)

- [x] 0.1 Python project scaffold (FastAPI app, pyproject.toml, project structure, .env.example) [A]
- [x] 0.2 DynamoDB table definitions + local provisioning script [A] (depends: 0.1)
- [x] 0.3 Telegram bot webhook endpoint stub in FastAPI [B] (depends: 0.1)
- [x] 0.4 AWS Bedrock client wrapper (Claude invoke, error handling, fallback templates) [B] (depends: 0.1)
- [x] 0.5 Config/secrets management (.env loading, API keys, bot token) [A] (depends: 0.1)

## Phase 1 — Onboarding + User Management (Day 1–2)

- [x] 1.1 DynamoDB data access layer (CRUD for User, RemittanceProfile, UserPreferences) [A] (depends: 0.2)
- [x] 1.2 Telegram message router (incoming webhook → handler dispatch) [B] (depends: 0.3)
- [x] 1.3 Onboarding conversation state machine (5-step flow) [B] (depends: 1.1, 1.2, 0.4)
- [x] 1.4 LLM-powered structured data extraction (parse free-text onboarding answers) [B] (depends: 0.4)
- [x] 1.5 Profile creation + confirmation flow [B] (depends: 1.3, 1.1)
- [x] 1.6 Preference update handler [B] (depends: 1.1, 0.4)

## Phase 2 — Rate Monitoring Engine (Day 2)

- [x] 2.1 FX API client (fetch rates, error handling, 5s timeout) [A] (depends: 0.5)
- [x] 2.2 CoinGecko API client (stablecoin prices USDC/USDT) [A] (depends: 0.5)
- [x] 2.3 Rate snapshot storage (write to DynamoDB RateSnapshot table) [A] (depends: 1.1, 2.1)
- [x] 2.4 Personal baseline calculator (14-day rolling average) [A] (depends: 2.3)
- [x] 2.5 Global baseline data (benchmark rates) [A] (depends: 2.1)
- [x] 2.6 Scheduler entry point (15-min polling cycle) [A] (depends: 2.3, 2.4)

## Phase 3 — Decision Engine + Alerts (Day 2–3)

- [x] 3.1 Rule engine: threshold evaluation [A] (depends: 2.4, 2.5)
- [x] 3.2 Payout optimization calculator [A] (depends: 2.1)
- [x] 3.3 Stablecoin route comparison [B] (depends: 2.2, 3.2)
- [x] 3.4 LLM explanation generator (adaptive to literacy level, fallback templates) [B] (depends: 0.4)
- [x] 3.5 Alert message formatter (full + short variants, stablecoin comparison) [B] (depends: 3.2, 3.3, 3.4)
- [x] 3.6 Alert cadence logic (first=full, subsequent=short, new window detection) [A] (depends: 3.1, 3.5)
- [x] 3.7 Proactive Telegram notification sender [B] (depends: 0.3, 3.5)
- [x] 3.8 Wire monitoring cycle to alert pipeline [A] (depends: 2.6, 3.1, 3.6, 3.7)

## Phase 4 — Transfer Execution / Wise Sandbox (Day 3–4)

- [x] 4.1 Wise sandbox OAuth flow (token exchange, storage, refresh) [A] (depends: 1.1, 0.5)
- [x] 4.2 Wise adapter: create_quote(), create_transfer(), get_transfer_status() [A] (depends: 4.1)
- [x] 4.3 Transfer confirmation flow (CONFIRM/WAIT/CANCEL, deduplication) [B] (depends: 1.2, 4.2)
- [x] 4.4 Transfer DynamoDB persistence + savings record computation [A] (depends: 1.1, 4.2, 2.4)
- [x] 4.5 Transfer status reporting to user [B] (depends: 4.2, 4.4, 3.4)
- [x] 4.6 Recommendation-only mode for non-US→India corridors [B] (depends: 1.2, 3.4)

## Phase 5 — Demo Polish + Integration Testing (Day 4–5)

- [x] 5.1 Seed FX rate data (14 days of snapshots) [A] (depends: 2.3)
- [x] 5.2 Mock Wise provider (deterministic transfer IDs) [A] (depends: 4.2)
- [x] 5.3 Deterministic replay mode [A] (depends: 2.6, 5.1)
- [ ] 5.4 End-to-end demo script test [B] (depends: all)
- [ ] 5.5 Multilingual output testing [B] (depends: 3.4)
- [ ] 5.6 Error handling sweep [A+B] (depends: all)

## Stretch Goals

- [ ] S.1 Monthly savings digest [B] (depends: 4.4, 3.4)
- [ ] S.2 Retry logic for failed provider API calls [A] (depends: 2.1, 4.2)
- [ ] S.3 Advanced preference commands [B] (depends: 1.6)
- [ ] S.4 Multi-corridor comparison [B] (depends: 2.1, 3.2)

---

## Review / Notes

### Implementation Summary
- All Phase 0–4 tasks implemented
- 30 Python files created across app/, scripts/, tests/
- 8/8 core tests passing
- FastAPI app starts with /health, /webhook/telegram, /wise/callback endpoints
- All modules syntax-checked and import-verified
- Dependencies installed via pyproject.toml

### Files Created
- `app/main.py` — FastAPI entry point (3 routes)
- `app/config.py` — Pydantic settings with .env loading
- `app/models/schemas.py` — 9 Pydantic models + 3 enums
- `app/db/dynamodb.py` — DynamoDB client wrapper
- `app/db/crud.py` — Full CRUD for all 7 tables
- `app/llm/bedrock.py` — Bedrock client (invoke + extract_structured)
- `app/llm/prompts.py` — System prompts + templates for all literacy levels
- `app/llm/fallbacks.py` — Template fallbacks when LLM unavailable
- `app/services/telegram.py` — Bot webhook + message routing
- `app/services/onboarding.py` — 5-step onboarding state machine
- `app/services/preference_handler.py` — NL preference parsing + updates
- `app/services/rate_monitor.py` — FX + rate snapshot storage + baselines
- `app/services/stablecoin.py` — CoinGecko client + route simulation
- `app/services/decision_engine.py` — Threshold eval + savings + cadence
- `app/services/recommendation.py` — LLM explanation + alert formatting
- `app/services/wise_adapter.py` — Wise OAuth + transfer API wrapper
- `app/services/transfer_handler.py` — CONFIRM/WAIT/CANCEL flow
- `app/services/mock_wise.py` — Deterministic mock provider
- `app/scheduler/monitor_job.py` — 15-min polling cycle
- `scripts/setup_dynamodb.py` — Table provisioning
- `scripts/seed_data.py` — 14-day demo data seeding
- `scripts/demo_replay.py` — Deterministic replay mode
- `tests/test_core.py` — 8 passing tests
