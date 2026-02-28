# RemitAgent — The Autonomous Remittance Guardian

**Technical Product Requirements Document (PRD)**
Version: v1.1 (Hackathon — Decisions Locked)
Status: Active Working PRD

### Team & Timeline
- **Team size:** 2 engineers
- **Timeline:** 3–5 days to demo-ready MVP
- **Scope strategy:** MVP first, stretch goals tracked separately

---

## 1. Product Overview

### 1.1 One-Line Summary

Messaging-first AI agent that monitors FX and fee conditions to maximize recipient payout, orchestrates sandboxed Wise transfers, and uses stablecoin route simulation for comparison — without custody of funds.

### 1.2 Problem Statement

Immigrant workers sending remittances face a set of persistent, overlooked challenges:

- High and opaque transfer fees
- Poor exchange timing decisions
- Cognitive overload from comparing providers
- Language barriers and limited time
- Requirement to manually monitor rates across multiple apps

RemitAgent addresses these by automatically monitoring rates, explaining opportunities clearly, and maximizing recipient payout — all through Telegram.

### 1.3 Target Impact

- Reduce effective transfer costs via timing optimization and routing
- Automate decision-making while preserving full user control
- Provide transparent savings reporting vs personal and global baselines

### 1.4 Why Now

- Telegram is a primary communication interface for many global users
- APIs from remittance providers and crypto rails are increasingly accessible
- LLM-based agents enable autonomous orchestration without heavy app infrastructure
- Serverless infrastructure enables low-cost continuous monitoring at scale

### 1.5 Core Product Principles

**User Choice First**
- Users are asked to choose configurable behaviors whenever possible
- LLM explains tradeoffs before choices are made
- System avoids making assumptions on behalf of users

**Transparent Defaults**
- If user skips a choice: system applies a safe default, clearly informs the user, and allows changes anytime

**Adaptive Explanation Level**
- Beginner (layman): outcome-focused language
- Intermediate: includes rate and fee concepts
- Advanced: technical details including spreads, effective FX rate, baseline modeling

**Progressive Disclosure**
- Explanations are short by default
- A clear "Want more detail?" option is always shown

**Progressive Onboarding**
- Only vital setup questions asked upfront
- Scenario-specific questions appear when relevant

**Best-Effort Continuity**
- Agent continues actions using transparent temporary defaults if information is missing

---

## 2. Users & Personas

### 2.1 Primary User — Immigrant Worker Sender

- Sends money regularly to family abroad
- Uses Telegram daily
- Limited time for financial optimization
- May have limited financial literacy

### 2.2 Secondary User — Family Member Recipient

- Receives funds via bank, wallet, or cash-out
- Needs clear updates in native language
- Low tolerance for uncertainty or delay

### 2.3 Jobs-to-be-Done

- "Tell me when to send money."
- "Send money safely without learning finance."
- "Show me how much I saved."
- "Keep my family informed automatically."

### 2.4 User Constraints

- Language diversity — multilingual support essential
- Low trust in financial systems
- Limited attention span — brevity required
- Telegram-only interaction — no native app required
- Device and storage limitations

---

## 3. Product Scope

### 3.1 MUST HAVE (Hackathon MVP)

- Telegram messaging interface
- Progressive onboarding (minimal friction)
- Financial literacy level selection
- Exchange-rate monitoring via external FX API (every 15 minutes)
- Snapshot storage every 15 minutes
- 14-day personal historical baseline
- Global remittance baseline comparison
- Stablecoin route simulation with live crypto API pricing (comparison/decision layer only — no execution)
- User-configurable alert sensitivity
- Immediate proactive alerts
- Wise OAuth (sandbox)
- Wise sandbox execution for US → India corridor
- Monitoring + recommendation for other global corridors (40+ countries)
- LLM-powered explanations via AWS Bedrock / Claude
- Multilingual output (LLM translation)

### 3.2 SHOULD HAVE (Stretch Goals)

- Monthly savings digest
- Retry logic for failed provider calls
- Advanced preference commands
- Multi-corridor comparison

### 3.3 OUT OF SCOPE

- Real money movement
- Real stablecoin transactions
- Custody of funds
- Building payment rails
- Full compliance stack
- Advanced fraud detection
- Native mobile app
- Real-time FX prediction models

### 3.4 Hackathon Success Criteria

- User can onboard via Telegram in under 60 seconds
- Agent monitors exchange rates autonomously
- Agent notifies user when favorable conditions occur
- User confirms transfer via message
- Transfer executes via Wise sandbox (US → India) or mocked provider
- Demo shows measurable "saved amount" vs baselines
- Infrastructure runs reliably during demo

---

## 4. Core User Flows

### 4.1 Progressive Onboarding (Vital Setup Only)

Required information collected upfront:

1. Preferred language
2. Financial literacy level
3. Sender country
4. Recipient country
5. Typical transfer amount

Monitoring begins immediately after these five inputs. Additional preferences (payout method, OAuth) are requested only when needed.

**Failure cases to handle:**
- User abandons onboarding mid-flow
- OAuth expires before use
- Unsupported corridor selected
- Session timeout after 24h inactivity

### 4.2 Profile Creation

1. Agent summarizes collected profile
2. User confirms or requests edits
3. Profile stored encrypted

Compliance note: KYC is handled by provider. Agent must not request sensitive identity data beyond necessary metadata.

### 4.3 Rate Monitoring + Snapshot Engine

Monitoring runs every 15 minutes:

1. Pull FX data from external API
2. Estimate recipient amount for each active corridor
3. Store rate snapshot
4. Compute personal baseline (average over last 14 days)
5. Compare against user threshold and global baseline
6. Trigger alert if favorable conditions met

**Personal baseline formula:**
```
personal_baseline = average(recipient_amount over last 14 days)
```

**Failure handling:**
- API unavailable: skip cycle, log error
- Stale rate data: flag and skip recommendation
- Skip cycle if response delay > 5 seconds

### 4.4 Transfer Recommendation

**Decision objective:**
```
maximize(recipient_amount)
```

**Where:**
```
recipient_amount = (amount_sent - estimated_fees) * effective_fx_rate
```

**Recommendation message structure:**
```
Recipient gets: ₹X
vs your 14-day average: +₹Y (+Z%)
vs global baseline: +₹A (+B%)

Want more detail?
Reply: 'Explain more' or 'Show technical details'
```

### 4.5 Alert Behavior

**Immediate Alerts**
Notify as soon as conditions meet threshold — no delay.

**Alert Cadence Logic**
- First alert in a favorable window: full message with all details
- Subsequent alerts in same window: short follow-up only

**Short follow-up format:**
```
Still a good time to send.
Recipient amount: ₹X (+Y%)
Reply 'details' for full breakdown.
```

**New Favorable Window Logic**

A new full alert is triggered when:
- A new threshold crossing occurs (rate re-enters favorable zone)
- User has interacted since last alert (CONFIRM, WAIT, questions, preference changes)

### 4.6 Transfer Execution Flow (Wise Sandbox — US → India Only)

1. User sends CONFIRM
2. Agent initiates Wise OAuth (if not already connected)
3. Agent calls Wise sandbox APIs:
   - `create_quote()`
   - `create_transfer()`
   - `get_transfer_status()`
4. Agent reports transfer ID and live status to user
5. Savings vs personal and global baseline displayed

### 4.7 Recommendation-Only Mode (All Other Corridors)

- Full rate monitoring active
- Recommendations sent with baselines
- If user confirms transfer: agent explains execution not yet enabled for this corridor
- Future expansion planned via multi-provider routing

### 4.8 Preference Updates via Chat

Users can modify any setting at any time. Examples:
- "Set explanation level to advanced."
- "Change alert sensitivity to 2%."
- "Switch to Intermediate explanations."

Agent confirms changes immediately and applies going forward.

### 4.9 Transfer Confirmation Flow

Agent sends recommendation. User replies:
- **CONFIRM** — initiates execution flow
- **WAIT** — agent acknowledges, continues monitoring
- **CANCEL** — monitoring continues, transfer aborted

**Failure cases:**
- Ambiguous user response: agent asks for clarification
- Duplicate confirmations: agent deduplicates

### 4.10 Monthly Savings Summary (Stretch)

1. Aggregate transfer history for the month
2. Compute baseline vs optimized rate
3. Generate summary message with total savings estimate

---

## 5. Feature Specifications

### 5.1 Messaging Onboarding

- Goal: Create usable profile via chat with minimal friction
- Interaction: Conversational Q&A, no long questionnaires
- Backend: Messaging webhook, user service
- Acceptance criteria: Profile created without UI forms in under 60 seconds

### 5.2 Adaptive Explanation System

**Beginner**
- Layman language, outcome-focused
- Example: "You'll save $12 if you send now instead of last week."

**Intermediate**
- Includes rate and fee concepts
- Example: "The exchange rate is 2% better than your 14-day average, saving you ₹840."

**Advanced**
- Full technical details: spreads, effective FX rate, baseline modeling methodology
- Example: "Effective rate 83.42 INR/USD vs 14-day avg 81.77 (spread: 1.65). Est. fees $4.99."

All levels: short explanations first, explicit "Want more detail?" option always shown.

### 5.3 Rate Monitoring Engine

- Goal: Detect favorable transfer windows automatically
- Runs every 15 minutes
- Polls external FX API, computes recipient amounts, stores snapshots
- Compares against personal 14-day baseline and global benchmark
- Acceptance criteria: Alert fires within one monitoring cycle of threshold being met

### 5.4 Transfer Recommendation Engine

- Goal: Explain decision clearly and drive user action
- Rule engine computes the decision; LLM explains it
- Fallback: default template if LLM call fails
- Acceptance criteria: User receives an understandable, actionable recommendation

### 5.5 Stablecoin Route Simulation

- Comparison only — no blockchain execution
- **Live pricing via crypto API** (CoinGecko or equivalent) for real-time stablecoin rates
- Shows estimated payout via stablecoin route (e.g., USD → USDC → local currency) vs traditional provider
- Helps user understand alternative routing options

### 5.6 Wise Sandbox Execution

- OAuth user account connection
- Sandbox transfer IDs returned and displayed
- Status tracked asynchronously
- US → India (USD → INR) corridor only for hackathon

### 5.7 Preference Education via LLM

- LLM explains alert sensitivity tradeoffs before user configures
- Explains implications of each option
- Guides user through feature choices conversationally

### 5.8 Savings Digest (Stretch)

- Monthly aggregate of transfer history
- Baseline vs optimized rate comparison
- Total saved estimate displayed

---

## 6. Technical Architecture

### 6.1 Technology Stack (Decided)

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| Database | DynamoDB |
| LLM | AWS Bedrock (Claude) |
| Messaging | Telegram Bot API |
| FX data | External FX API (key available) |
| Crypto pricing | CoinGecko API (live stablecoin rates) |
| Transfer provider | Wise sandbox (credentials TBD) |
| Infrastructure | AWS serverless (Lambda + EventBridge) |
| Repo structure | Single-repo monolith |

### 6.2 Component Overview

- **Telegram Bot** — primary messaging interface
- **FastAPI Webhook API** — ingests messages, triggers orchestration
- **Agent Orchestrator** — event-driven, stateless execution with persisted memory
- **Rule-Based Decision Engine** — threshold evaluation, payout optimization
- **LLM Explanation Layer** — AWS Bedrock / Claude; interprets and explains
- **Rate Monitoring Service** — scheduled, polls FX APIs every 15 min
- **Stablecoin Routing Simulator** — live crypto API pricing, comparison layer only
- **Wise Adapter** — sandbox OAuth + transfer APIs
- **OAuth Service** — token management
- **DynamoDB Data Store** — encrypted at rest

### 6.3 Intelligence Model

```
Rule Engine  →  computes decisions (triggers, thresholds, payout math)
LLM          →  explains + interprets + translates
```

No hardcoded NLP required. LLM handles intent classification and natural language.

### 6.4 Agent Orchestration Model

- Event-driven architecture
- Stateless execution with persisted memory (user profile + conversation state)
- Task queue for async actions (transfer status, notifications)

### 6.5 Transfer Execution Layer

Provider adapter pattern with unified interface:
```
create_transfer()
check_status()
```
Supports Wise sandbox today, extensible for additional providers.

### 6.6 Security Model

- OAuth tokens encrypted at rest
- No custody of funds
- Minimal PII storage
- Audit logs
- Access controls

### 6.7 Infrastructure

- AWS serverless (Lambda + EventBridge scheduler)
- DynamoDB for data persistence
- CloudWatch for logging
- Single-repo Python monolith for hackathon; CI/CD optional

---

## 7. Data Model

### User
| Field | Type |
|---|---|
| user_id | string |
| language | string |
| timezone | string |
| created_at | timestamp |

### RemittanceProfile
| Field | Type |
|---|---|
| profile_id | string |
| user_id | string |
| sender_country | string |
| recipient_country | string |
| corridor | string |
| average_amount | float |
| payout_method | string |
| execution_enabled | bool |

### UserPreferences
| Field | Type |
|---|---|
| financial_literacy_level | enum (beginner, intermediate, advanced) |
| alert_threshold_pct | float |
| defaults_applied | bool |

### RateSnapshot
| Field | Type |
|---|---|
| snapshot_id | string |
| corridor | string |
| provider | string |
| rate | float |
| recipient_amount | float |
| timestamp | timestamp |

### Transfer
| Field | Type |
|---|---|
| transfer_id | string |
| user_id | string |
| provider | string |
| amount | float |
| fx_rate | float |
| status | string |
| provider_tx_id | string |

### SavingsRecord
| Field | Type |
|---|---|
| user_id | string |
| transfer_id | string |
| baseline_rate | float |
| optimized_rate | float |
| personal_savings | float |
| global_savings | float |

**Relationships:** User 1:N Transfers, User 1:1 RemittanceProfile, Transfer → SavingsRecord

---

## 8. AI / Agent Design

### 8.1 LLM Responsibilities

- Intent classification from natural language input
- Explanation generation (adaptive to literacy level)
- Preference education and tradeoff explanation
- Multilingual translation and output
- Progressive disclosure management
- Structured data extraction during onboarding

### 8.2 Rule Engine Responsibilities

- Trigger detection (threshold crossing)
- Payout optimization math
- Threshold evaluation against baselines
- Alert cadence logic

### 8.3 Missing Info Logic

```
if preference_missing:
    apply_safe_default()
    explain_default_to_user()
    continue_action()
```

### 8.4 Memory Model

- Persistent structured profile (user, preferences, corridor)
- Short-term conversation context
- No long-term raw chat logs stored

### 8.5 Agent Guardrails

- Never initiate transfer without explicit user confirmation
- Never ask for sensitive credentials or identity documents
- Avoid financial advice language — position as execution assistant
- LLM only explains; rule engine decides

### 8.6 Prompt Structure

- System prompt: compliance constraints and agent role
- Tool calls for rate lookup and transfer execution
- Output templates enforced for consistent messaging

---

## 9. Engineering Implementation Plan

**Phase 0 — Setup (Day 1 morning)**
- Python project scaffolding (FastAPI, dependencies, project structure)
- Telegram bot webhook configuration
- AWS infrastructure bootstrap (DynamoDB tables, Lambda, EventBridge)
- Wise sandbox account and API credentials setup (TBD)
- Repo setup, Git workflow established

**Phase 1 — Progressive Onboarding + Preferences (Day 1–2)**
- FastAPI webhook endpoint for Telegram messages
- Conversation state machine for onboarding flow
- DynamoDB user/profile storage
- AWS Bedrock integration for LLM-powered onboarding extraction

**Phase 2 — Rate Monitoring Engine (Day 2)**
- FX API integration (API key ready)
- CoinGecko API integration for stablecoin route pricing
- EventBridge scheduler with 15-minute polling
- DynamoDB snapshot storage and corridor grouping

**Phase 3 — Agent Logic + Decision System (Day 2–3)**
- Trigger rules and threshold evaluation
- Recommendation generation with baseline comparisons
- Stablecoin vs traditional route comparison logic
- Notification formatting (full and short alert variants)
- Bedrock/Claude explanation generation (adaptive to literacy level)

**Phase 4 — Wise Execution Integration (Day 3–4)**
- Provider OAuth flow (sandbox)
- Transfer API wrapper (create_quote, create_transfer, get_status)
- Async status tracking

**Phase 5 — Demo Polish (Day 4–5)**
- Demo scripts and seed FX rate data
- Deterministic replay mode for API failure fallback
- End-to-end testing of full flow
- Failure simulation and edge case handling

---

## 10. Engineering Task Breakdown

**Backend (Python + FastAPI)**
- [ ] FastAPI app scaffold and project structure
- [ ] Telegram webhook endpoint
- [ ] User service (DynamoDB)
- [ ] Profile service (DynamoDB)
- [ ] Transfer service (DynamoDB)
- [ ] FX rate ingestion pipeline
- [ ] CoinGecko stablecoin pricing integration

**Agent / AI (AWS Bedrock)**
- [ ] System prompt design
- [ ] Structured extraction parser (onboarding)
- [ ] Recommendation generator (LLM + rule engine)
- [ ] Multilingual output via Bedrock Claude

**Messaging Integration**
- [ ] Telegram bot setup and webhook routing

**Infrastructure (AWS)**
- [ ] DynamoDB table provisioning
- [ ] Lambda functions + EventBridge scheduler (15-min polling)
- [ ] Secrets Manager for OAuth tokens and API keys

**Security**
- [ ] Token encryption at rest (DynamoDB + KMS)
- [ ] Audit logs
- [ ] Access controls

**Demo Tooling**
- [ ] Seed FX data
- [ ] Mock provider mode (Wise fallback)
- [ ] Deterministic replay script

---

## 11. Demo Strategy

### 11.1 Demo Corridor

US → India (USD → INR) — primary demo corridor for Wise sandbox execution.

### 11.2 Ideal Demo Script

1. User onboards via Telegram in under 60 seconds
2. Agent announces rate monitoring has begun
3. Favorable rate opportunity detected — full alert sent
4. User sends CONFIRM
5. Wise sandbox OAuth connected
6. Sandbox transfer created — transfer ID returned
7. Savings vs personal 14-day average and global baseline displayed

### 11.3 The Wow Moment

Agent proactively messages the user:
```
If you send now, you save $12.40 compared to your 14-day average.
Recipient gets ₹83,420 — ₹1,380 more than last week.
```

### 11.4 Fallback Demo (API Failure)

- Use mocked provider with pre-seeded transfer IDs
- Replay stored rate data deterministically
- All key flows still demonstrable offline

---

## 12. Metrics & Validation

### 12.1 Core Demo Metrics

- Time-to-onboard (target: < 60 seconds)
- Alert engagement rate
- Transfer confirmation rate
- End-to-end flow completion rate

### 12.2 User Savings Metrics

- Personal savings vs 14-day baseline
- Global savings vs benchmark
- Average % improvement per transfer

### 12.3 System Reliability Metrics

- Monitoring job success rate
- Messaging delivery success rate
- API failure rate and recovery

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Alert fatigue | User-configurable sensitivity + short follow-up alerts after first in window |
| Missing preferences | Best-effort continuation with transparent defaults |
| Wise sandbox instability | Deterministic replay mode with pre-seeded data |
| Regulatory misinterpretation | Strict "execution assistant" language; avoid "advice" framing |
| Telegram API issues | Tested early in Phase 0; fallback to mock mode |

---

## 14. Future Extensions

**Post-Hackathon Roadmap**
- Multi-provider optimization (Wise + Stellar anchors + others)
- Real stablecoin rails for qualifying corridors
- Smart recurring transfer automation
- Corridor-specific intelligence and seasonal patterns
- Notification cooldown and smart scheduling
- Auto-confirm rules with user-defined limits
- Family budgeting insights
- Advanced analytics dashboard

**Monetization Paths**
- Referral fees from providers
- Premium optimization tier
- B2B remittance optimization platform

---

## 15. Resolved Decisions

| Decision | Resolution |
|---|---|
| Backend language/framework | Python + FastAPI |
| Data store | DynamoDB |
| LLM provider | AWS Bedrock (Claude) |
| Stablecoin simulation depth | Live crypto API pricing (CoinGecko) |
| Team size | 2 engineers |
| Timeline | 3–5 days |
| Scope | MVP + stretch goals tracked separately |

### Credentials Status

| Credential | Status |
|---|---|
| Telegram Bot token | Ready |
| AWS account + Bedrock access | Ready |
| FX rate API key | Ready |
| Wise sandbox API credentials | Not yet set up |

## 16. Open Questions

**Product Decisions**
- Action buttons vs typed responses — which UX is better for Telegram?
- Notification cooldown period — how long to wait before re-alerting in the same window?
- Should the agent auto-confirm recurring transfers under predefined rules?
- Additional user preference settings to surface during onboarding?

**Technical Decisions**
- ~~Preferred backend data store: DynamoDB vs PostgreSQL?~~ → **DynamoDB**
- Should LLM be allowed to influence timing decisions, or only explain rule-based outcomes?
- Conversation log retention policy for compliance?
- Will demo require live external API calls, or is deterministic replay acceptable to judges?

**Compliance / Legal**
- Confirm "execution assistant" vs "financial advisor" language with team
- Any constraints on storing conversation logs for the demo?
- What KYC/AML disclosures are needed in the onboarding flow?
