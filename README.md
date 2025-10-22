# Real Estate Scout – CrewAI + LoopNet

A **simple, runnable Python project** that queries LoopNet via RapidAPI, runs a multi-agent CrewAI analysis on each listing, and produces **1–100 scores** plus a consolidated investment memo.

## 🎯 Features

- **LoopNet Integration**: Query commercial real estate listings via RapidAPI
- **Multi-Agent Analysis**: 5 specialist agents + 1 aggregator
  - Investment Analyst (30% weight)
  - Location Risk (25% weight)
  - News/Community Signals (10% weight)
  - VC Risk/Return (20% weight)
  - Construction Scope (15% weight)
- **Structured Scoring**: Each agent outputs 1–100 score + rationale + notes
- **Final Report**: Overall weighted score + markdown memo (<= 1 page)
- **CLI & API**: Rich terminal interface + FastAPI endpoints
- **Serper News Signals**: Pulls local headlines via Serper with graceful degradation when the API key is missing
- **LA Open Data Bundle**: Socrata-backed permits, inspections, COO, and code enforcement ingestion for Los Angeles addresses

## 📋 Prerequisites

- Python 3.11+
- RapidAPI key for LoopNet API
- OpenAI API key (for CrewAI agents)
- Serper API key (https://serper.dev) for richer news signals (optional; falls back to neutral scoring when absent)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
#   RAPIDAPI_KEY=your_rapidapi_key
#   OPENAI_API_KEY=your_openai_key
```

### 3. Run CLI Analysis

```bash
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --size 10 \
  --price-min 500000 \
  --price-max 3000000
```

**Output**: Pretty table in terminal + JSON + Markdown files in `./out/`

> 💡 Tip: Run `python -m src.cli analyze --use-stored --size 5` to reuse the saved filters in `config/filters.json`. Add `--persist-filters` to write any CLI overrides back to disk.

### 4. Run FastAPI Server

```bash
uvicorn src.main:app --reload
```

**Endpoints**:
- `GET /health` – Health check
- `GET /filters` – Fetch stored LoopNet search filters
- `POST /filters` – Update filters via JSON payload
- `POST /filters/reset` – Restore default filters
- `GET /filters/ui` – Browser-based filter editor with inline CSS
- `POST /analyze` – Analyze listings (request body optional; omit to use stored filters or set `use_stored=true`)

Example request (ad-hoc body):
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "locationId": "41096",
    "locationType": "city",
    "page": 1,
    "size": 5,
    "priceMin": 500000,
    "priceMax": 3000000
  }'
```

Use the stored filters without a body:
```bash
curl -X POST "http://localhost:8000/analyze?use_stored=true"
```

## 🎛️ Filter Manager

- Filters are persisted to `config/filters.json` and reused by the API, CLI, and UI.
- Visit `http://localhost:8000/filters/ui` for a lightweight HTML form with inline styles—no build step required.
- Submit the form to save changes or click **Reset Defaults** to restore the starter configuration.
- Prefer JSON automation? Call `POST /filters` with a `FilterUpdate` payload or `POST /filters/reset` to restore defaults programmatically.

## 📁 Project Structure

```
.
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment settings
│   │   ├── models.py           # Pydantic schemas
│   │   ├── loopnet_client.py   # LoopNet API client (HTTPX + retries)
│   │   ├── la_socrata.py       # LA Open Data (Socrata) fetcher
│   │   ├── crew.py             # CrewAI orchestration
│   │   ├── scoring.py          # Score normalization & weighting
│   │   └── tools.py            # Optional helper tools
│   ├── agents/
│   │   ├── investor.py         # Long-term investment analyst
│   │   ├── location_risk.py    # Location trajectory analyst
│   │   ├── news_reddit.py      # News/community signals
│   │   ├── vc_risk_return.py   # Risk/return architect
│   │   ├── construction.py     # Construction scope analyst
│   │   ├── aggregator.py       # Final memo writer
│   │   └── la_property_ingestor.py  # LA City Socrata ingestion agent
│   ├── cli.py                  # Rich CLI interface
│   └── main.py                 # FastAPI application
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## 🧠 Agent Scoring System

Each agent returns:
```python
{
  "score_1_to_100": int,      # 1-100 integer score
  "rationale": str,            # Short explanation
  "notes": list[str]           # 3-6 key points
}
```

**Final Report** includes:
- Individual scores from all 5 specialist agents
- **Overall score**: Weighted average (1-100)
- **Markdown memo**: Deal snapshot, risks, thesis, go/no-go

## 🔐 Security

- **Never commit API keys** – Use `.env` file (gitignored)
- Keys loaded from environment variables at runtime
- `.env.example` provided as template

## 🛠️ Implementation Notes

- **Retry Logic**: Tenacity with exponential backoff for LoopNet API (429/5xx handling)
- **Crew Execution**: CrewAI runs inside a background thread so FastAPI endpoints stay responsive
- **Minimal Dependencies**: No ORM, no complex abstractions
- **Extensible**: Add optional geocoding/news APIs via `tools.py`
- **Serper Integration**: `src/app/serper_news.py` hits `https://google.serper.dev/news` with retries and graceful fallback when `SERPER_API_KEY` is missing
- **LA Socrata Ingestion**: `src/app/la_socrata.py` + `src/agents/la_property_ingestor.py` bundle permits, inspections, COO, and code enforcement data into one JSON blob for downstream agents

## 📊 Example Output

```
┌─────────────────────────┬──────────┬────────┬──────────┬─────────┬──────────┬──────────┬─────────┐
│ Address                 │ Ask      │ Invest │ Location │ News    │ VC Risk  │ Constr.  │ Overall │
├─────────────────────────┼──────────┼────────┼──────────┼─────────┼──────────┼──────────┼─────────┤
│ 123 Main St, Austin, TX │ $1.2M    │ 78     │ 82       │ 65      │ 70       │ 75       │ 76      │
│ 456 Oak Ave, Austin, TX │ $2.5M    │ 85     │ 88       │ 72      │ 80       │ 82       │ 82      │
└─────────────────────────┴──────────┴────────┴──────────┴─────────┴──────────┴──────────┴─────────┘
```

Reports saved to:
- `./out/listing_<id>.json`
- `./out/listing_<id>.md`

## 🔮 Future Extensions

- Geocoding + walk score integration
- News API / Reddit scraping (when keys available)
- Historical data caching (JSON files)
- Email/Slack notifications for high-scoring deals

## 📝 License

MIT – Use freely for personal or commercial projects.
