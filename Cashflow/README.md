# Cashflow Forecasting

Production-grade cash flow forecasting application built from the CRISIL requirements. Upload historical monthly Excel data, generate 2026 forecasts, run scenario analysis, and query via natural-language prompts.

## Features

- **Data ingestion** — Excel upload with column auto-mapping and validation guardrails
- **Cash flow engine** — Historical cash flow from derived ratios (Step 2 formulas)
- **2026 base forecast** — ARIMA predictive models per financial series (auto order selection via AIC)
- **Scenario analysis** — Delayed receivables, increased supplier payout, combined stress test
- **Natural-language prompts** — Routes forecast/scenario intents; free-form questions go to **OpenAI GPT**
- **Insights** — Seasonal patterns plus GPT-generated liquidity risk narrative
- **AI advisory** — Cashflow improvement and risk writeups grounded in your uploaded data
- **Excel export** — Download forecast and scenario workbooks
- **Production guardrails** — Input validation, file size limits, outlier detection, structured logging, health checks

## Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys))

The UI is pre-built in `frontend/dist` and served by the Python backend — **Node.js is not required to run the app**.

### 1. Generate sample data

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pandas openpyxl
python ../scripts/generate_sample_data.py
```

### 2. Start the app (recommended)

From the repo root — picks the first free port from **8000**:

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

Open http://localhost:8000 — upload `sample_data/sample_data_foundry.xlsx`.

### Manual start

```bash
cd backend
source .venv/bin/activate
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

App UI: http://localhost:8000  
API docs: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/data/upload` | Upload Excel file |
| GET | `/api/v1/data/history` | Historical data + cash flow |
| POST | `/api/v1/forecast/base` | 2026 base forecast |
| POST | `/api/v1/forecast/trend` | Next N months trend |
| POST | `/api/v1/forecast/scenarios` | Scenario comparison |
| POST | `/api/v1/prompt` | Natural-language prompt router |
| GET | `/api/v1/insights` | Seasonal insights + GPT risk narrative |
| GET | `/api/v1/llm/status` | OpenAI connection and model status |
| GET | `/api/v1/export/forecast` | Download forecast Excel |
| GET | `/api/v1/export/scenarios` | Download scenarios Excel |

## Guardrails

- Minimum **12 months** of history required
- **5 MB** max upload size
- Column presence and numeric type validation
- Cross-field consistency checks (sales = credit + cash, etc.)
- Outlier detection (>4σ)
- Forecast output sanity checks
- Request ID tracing (`X-Request-ID`)
- Structured JSON logging
- Global error handlers (no stack trace leakage in production)

## Tests

```bash
cd backend
pytest -v
```

## Excel Column Format

| Column | Required |
|--------|----------|
| Month | Yes (e.g. `Jan-23`) |
| Total Sales | Yes |
| Total Credit Sales | Yes |
| Total Cash Sales | Yes |
| Collections | Yes |
| Total Expenses | Yes |
| Total Cash Expenses | Yes |
| Total Credit Expenses | Yes |
| Cash Paid for Credit Expenses | Yes |

## OpenAI Configuration

Set these in `backend/.env` (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_ENABLED` | `true` | Set `false` to use rule-based insights only |
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT model for narratives and advisory |
| `OPENAI_TIMEOUT_SECONDS` | `120` | Max wait per advisory request |
| `OPENAI_BASE_URL` | *(optional)* | Override API base URL (e.g. Azure OpenAI) |

Check status: `GET /api/v1/llm/status`

When configured, the Advisory Assistant sends your treasury data (ratios, forecasts, scenarios, insights) as context so the model answers with your numbers — not generic advice.

## Frontend development (optional)

To change the React UI, install Node.js 20+ and rebuild:

```bash
cd frontend
npm install
npm run build
```

Then restart the backend — it serves the updated files from `frontend/dist`.

## Prompt Examples

- *"Give me cash flow for the next 5 months based on historical trends."*
- *"Generate a cash flow forecast for the year 2026, expecting a 5% increase in total sales."*
- *"Now, give me cash-flow forecast for these scenarios with delayed receivable by 30 days."*
- *"Can you analyse the key factors for positive cash flow during low seasons?"*
