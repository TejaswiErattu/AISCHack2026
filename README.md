# RemitAgent

Messaging-first AI agent that monitors FX rates, optimizes transfer timing, and orchestrates sandboxed Wise transfers — all through Telegram.

## Prerequisites

- Python 3.11+
- AWS account with Bedrock access (Claude model enabled)
- Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- [ExchangeRate-API](https://www.exchangerate-api.com/) key
- Wise sandbox credentials (optional — mock provider available)
- DynamoDB (AWS-hosted or [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) for development)

## Quick Start

### 1. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2. Configure environment

Create a `.env` file in the project root and fill in your credentials:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `AWS_REGION` | Yes | AWS region (default: `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | Yes | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS IAM secret key |
| `BEDROCK_MODEL_ID` | Yes | Bedrock model ID (default: `anthropic.claude-3-5-sonnet-20241022-v2:0`) |
| `FX_API_KEY` | Yes | ExchangeRate-API key |
| `WISE_API_TOKEN` | No | Wise sandbox personal API token |
| `DYNAMODB_ENDPOINT_URL` | No | Set to `http://localhost:8000` for DynamoDB Local |

### 3. Provision DynamoDB tables

```bash
python -m scripts.setup_dynamodb
```

This creates all 7 tables: `users`, `remittance_profiles`, `user_preferences`, `rate_snapshots`, `transfers`, `savings_records`, `alert_states`.

For local development with DynamoDB Local:

```bash
# Start DynamoDB Local (Docker)
docker run -p 8000:8000 amazon/dynamodb-local

# Set endpoint in .env
DYNAMODB_ENDPOINT_URL=http://localhost:8000

# Then provision tables
python -m scripts.setup_dynamodb
```

### 4. Set up Telegram webhook

Register your webhook URL with Telegram (replace with your public URL or use [ngrok](https://ngrok.com/) for local dev):

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_DOMAIN>/webhook/telegram"
```

For local development with ngrok:

```bash
ngrok http 8080
# Then set the webhook to the ngrok HTTPS URL
```

### 5. Run the app

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`. Verify with:

```bash
curl http://localhost:8080/health
```

## Demo Mode

### Seed historical rate data

Pre-populate 14 days of FX snapshots so the baseline calculator works immediately:

```bash
python -m scripts.seed_data
```

### Deterministic replay

Replay a scripted rate sequence when APIs are unavailable:

```bash
python -m scripts.demo_replay
```

## Running Tests

```bash
pytest -v
```

## Project Structure

```
app/
  main.py                  # FastAPI entry point (/health, /webhook/telegram, /wise/callback)
  config.py                # Settings via pydantic-settings + .env
  models/
    schemas.py             # Pydantic models (User, RemittanceProfile, Transfer, etc.)
  db/
    dynamodb.py            # DynamoDB client wrapper
    crud.py                # CRUD operations for all 7 tables
  llm/
    bedrock.py             # AWS Bedrock client (Claude invoke + structured extraction)
    prompts.py             # System prompts + explanation templates
    fallbacks.py           # Template fallbacks when LLM is unavailable
  services/
    telegram.py            # Bot webhook handler + message routing
    onboarding.py          # 5-step onboarding conversation state machine
    preference_handler.py  # Natural language preference updates
    rate_monitor.py        # FX API client + snapshot storage + baseline calc
    stablecoin.py          # CoinGecko client + stablecoin route simulation
    decision_engine.py     # Threshold evaluation + payout optimization + alert cadence
    recommendation.py      # LLM explanation generation + alert formatting
    wise_adapter.py        # Wise sandbox OAuth + transfer API
    transfer_handler.py    # CONFIRM / WAIT / CANCEL flow
    mock_wise.py           # Deterministic mock provider for demos
  scheduler/
    monitor_job.py         # 15-minute rate monitoring cycle
scripts/
  setup_dynamodb.py        # Table provisioning
  seed_data.py             # Seed 14 days of FX snapshots
  demo_replay.py           # Deterministic rate replay
tests/
  test_core.py             # Core unit tests
```

## Architecture

```
Telegram  -->  FastAPI Webhook  -->  Message Router
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
               Onboarding         Rate Monitor        Transfer Flow
                    |                   |                   |
               Bedrock LLM        Decision Engine      Wise Sandbox
                    |                   |                   |
               DynamoDB            Alert Pipeline       Savings Record
```

- **Rule engine** computes decisions (thresholds, payout math, alert cadence)
- **LLM (Bedrock Claude)** explains and translates — never decides
- **Stablecoin simulator** provides comparison data via CoinGecko (no execution)
- Transfer execution is limited to **US → India (USD → INR)** via Wise sandbox

## AWS Lambda Deployment

The app includes a Mangum handler for Lambda deployment:

```python
# app/main.py
from mangum import Mangum
handler = Mangum(app, lifespan="off")
```

Deploy with your preferred method (SAM, CDK, Serverless Framework) and set the Lambda handler to `app.main.handler`. Use EventBridge to schedule the monitoring job every 15 minutes.
