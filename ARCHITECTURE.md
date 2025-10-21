# Real Estate Scout - Project Architecture

## Overview

This is a **simple, production-ready** CrewAI application that:
1. Fetches commercial real estate listings from LoopNet via RapidAPI
2. Runs 5 specialist AI agents + 1 aggregator to analyze each property
3. Outputs structured 1-100 scores and markdown investment memos
4. Provides both CLI and REST API interfaces

**Design Philosophy:** Keep it simple, runnable, and extensible. No over-engineering.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                      │
├──────────────────────┬──────────────────────────────────────┤
│   CLI (Rich)         │         FastAPI REST API             │
│   src/cli.py         │         src/main.py                  │
└──────────┬───────────┴────────────────┬─────────────────────┘
           │                            │
           └──────────┬─────────────────┘
                      │
           ┌──────────▼──────────┐
           │   Search Params     │
           │   (Pydantic)        │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │  LoopNet Client     │
           │  (HTTPX + Retry)    │
           │  src/app/           │
           │  loopnet_client.py  │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │   Listings (raw)    │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────────────────┐
           │   PropertyAnalysisCrew          │
           │   (CrewAI Orchestrator)         │
           │   src/app/crew.py               │
           └──────────┬──────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   ┌───▼───┐     ┌───▼───┐     ┌───▼───┐
   │Agent 1│     │Agent 2│ ... │Agent 5│
   │Invest │     │Locatn │     │Constr │
   └───┬───┘     └───┬───┘     └───┬───┘
       │             │             │
       └──────┬──────┴──────┬──────┘
              │             │
       ┌──────▼─────────────▼─────-─┐
       │   Aggregator Agent         │
       │   (Final Memo Writer)      │
       └──────────┬─────────────────┘
                  │
       ┌──────────▼─────────────┐
       │  FinalReport           │
       │  - Scores (1-100)      │
       │  - Markdown Memo       │
       │  - JSON Export         │
       └────────────────────────┘
```

---

## File Structure

```
real-estate-scout/
│
├── src/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── cli.py                   # Rich CLI interface
│   ├── main.py                  # FastAPI application
│   │
│   ├── app/                     # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py            # Settings (env vars)
│   │   ├── models.py            # Pydantic schemas
│   │   ├── loopnet_client.py   # API client (HTTPX + Tenacity)
│   │   ├── crew.py              # CrewAI orchestration
│   │   ├── scoring.py           # Score normalization & weighting
│   │   └── tools.py             # Helper tools (stubs)
│   │
│   └── agents/                  # AI agent definitions
│       ├── __init__.py
│       ├── investor.py          # Investment analyst
│       ├── location_risk.py     # Location trajectory
│       ├── news_reddit.py       # News/community signals
│       ├── vc_risk_return.py    # Risk/return architect
│       ├── construction.py      # Construction scope
│       └── aggregator.py        # Final memo writer
│
├── .env.example                 # Template for secrets
├── .gitignore                   # Git ignore rules
├── pyproject.toml               # Package configuration
├── requirements.txt             # Dependencies (alternative)
├── README.md                    # Main documentation
├── SETUP.md                     # Setup guide
├── ARCHITECTURE.md              # This file
└── verify_setup.py              # Setup verification script
```

---

## Data Flow

### 1. User Input → Search Parameters
- **CLI**: Parses arguments (`--location-id`, `--price-min`, etc.)
- **API**: Receives JSON POST body
- **Output**: `SearchParams` Pydantic model

### 2. Search Parameters → LoopNet API
- **Client**: `LoopNetClient` (HTTPX with Tenacity retry)
- **Endpoint**: `POST /loopnet/sale/advanceSearch`
- **Retry Logic**: Exponential backoff on 429/5xx
- **Output**: List of `Listing` objects

### 3. Listings → Multi-Agent Analysis
- **Orchestrator**: `PropertyAnalysisCrew`
- **Process**:
  1. Format listing data for agents
  2. Create 5 specialist tasks (parallel execution)
  3. Run CrewAI crew
  4. Parse JSON outputs → `AgentOutput` objects
  5. Calculate weighted overall score
  6. Run aggregator agent for final memo
- **Output**: `FinalReport` per listing

### 4. Final Reports → User
- **CLI**: Pretty table (Rich) + JSON/MD files saved to disk
- **API**: JSON array of `FinalReport` objects
- **Files**: `listing_<id>.json` + `listing_<id>.md`

---

## Agent Design

### Specialist Agents (5)

Each specialist agent:
- Has a clear role and expertise area
- Receives formatted listing context
- Returns **structured JSON**:
  ```json
  {
    "score_1_to_100": 75,
    "rationale": "2-3 sentence explanation",
    "notes": ["bullet 1", "bullet 2", "bullet 3"]
  }
  ```
- Uses conservative scoring (better to underestimate)

**Agents:**
1. **Investment Analyst (30% weight)**
   - Cash flow resilience
   - Downside protection
   - Exit liquidity

2. **Location Risk (25% weight)**
   - Demographics & trajectory
   - Transit/walkability
   - Regulatory risks

3. **VC Risk/Return (20% weight)**
   - Risk identification
   - Concrete mitigations
   - Adjusted attractiveness

4. **Construction (15% weight)**
   - Scope estimation
   - Cost bands ($/SF)
   - Timeline & disruption

5. **News Signals (10% weight)**
   - Policy changes
   - Community sentiment
   - Nuisance issues

### Aggregator Agent

- **Input**: All 5 specialist outputs + calculated overall score
- **Output**: Investment memo (markdown) with:
  - Deal snapshot
  - Score table
  - Top 5 risks & mitigations
  - Red flags
  - Investment thesis
  - Go/No-Go recommendation

---

## Key Design Decisions

### 1. Why Pydantic?
- **Type Safety**: Catch errors at model validation, not runtime
- **Settings Management**: `pydantic-settings` for env vars
- **API Contracts**: FastAPI auto-generates OpenAPI docs

### 2. Why HTTPX + Tenacity?
- **Async Support**: Better performance for parallel requests
- **Retry Logic**: Automatic backoff for rate limits
- **Simplicity**: No need for full SDK

### 3. Why CrewAI?
- **Multi-Agent Orchestration**: Built-in task management
- **LLM Integration**: Works with OpenAI out-of-the-box
- **Sequential/Parallel**: Flexible execution modes

### 4. Why Rich?
- **Beautiful CLI**: Professional terminal output
- **Progress Bars**: User feedback during long operations
- **Tables**: Clean data presentation

### 5. Why FastAPI?
- **Auto Docs**: Swagger UI at `/docs`
- **Pydantic Native**: Seamless integration
- **Async**: Non-blocking I/O for multi-agent tasks

---

## Scoring System

### Individual Scores (1-100)
- **80-100**: Exceptional (green flag)
- **60-79**: Good (yellow/positive)
- **40-59**: Average (neutral)
- **20-39**: Below average (orange/caution)
- **1-19**: Poor (red flag)

### Overall Score Calculation
```python
overall = round(
    investment * 0.30 +
    location * 0.25 +
    vc_risk * 0.20 +
    construction * 0.15 +
    news * 0.10
)
```

### Weights Rationale
- **Investment (30%)**: Most critical - cash flow is king
- **Location (25%)**: Hard to change, drives long-term value
- **VC Risk (20%)**: Risk management = risk-adjusted returns
- **Construction (15%)**: Capex impacts ROI significantly
- **News (10%)**: Lagging indicator, often overblown

**Customizable**: Edit `.env` to adjust weights.

---

## Error Handling

### API Client Errors
- **429 Rate Limit**: Retry with exponential backoff (3 attempts)
- **5xx Server**: Retry with exponential backoff (3 attempts)
- **4xx Client**: Raise immediately, no retry
- **Timeout**: Retry with exponential backoff (3 attempts)

### Agent Parsing Errors
- **Malformed JSON**: Default to neutral score (50) + error note
- **Missing Fields**: Use default values from Pydantic
- **Extraction**: Try multiple patterns (code blocks, raw JSON)

### API Endpoint Errors
- **Missing Keys**: 500 with clear message
- **LoopNet Errors**: 502 with error detail
- **Agent Failures**: Continue processing other listings

---

## Extensibility

### Adding New Agents
1. Create `src/agents/new_agent.py`
2. Define agent with `create_new_agent()`
3. Add task template (prompt)
4. Update `src/app/crew.py` to include new agent
5. Update weights in `config.py`

### Adding External APIs
1. Implement function in `src/app/tools.py`
2. Call from agent prompt (or pass as tool)
3. Handle errors gracefully (return None if unavailable)

### Custom Scoring Logic
- Modify `src/app/scoring.py`
- Keep functions pure (no side effects)
- Always clamp to 1-100 range

---

## Performance Considerations

### Current
- **Sequential**: Listings processed one-by-one
- **Parallel Agents**: 5 specialists run concurrently per listing
- **Bottleneck**: OpenAI API rate limits

### Optimizations (Future)
- **Batch Processing**: `asyncio.gather()` for multiple listings
- **Caching**: Store LoopNet responses to avoid re-fetching
- **Agent Pooling**: Reuse agent instances across requests
- **Streaming**: Stream responses as they complete

---

## Security

### API Keys
- **Never commit** real keys to git
- Use `.env` file (gitignored)
- Validate at startup (fail fast)

### Input Validation
- Pydantic models validate all inputs
- Clamp numeric ranges (price, size, etc.)
- Sanitize file paths for output

### Rate Limiting (Future)
- Add rate limiter to FastAPI endpoints
- Prevent abuse of expensive agent runs

---

## Testing Strategy (Future)

### Unit Tests
- `test_scoring.py`: Normalize, clamp, weighted average
- `test_models.py`: Pydantic validation
- `test_client.py`: Mock LoopNet responses

### Integration Tests
- `test_crew.py`: Full agent pipeline with fixtures
- `test_api.py`: FastAPI endpoints with TestClient

### End-to-End
- `test_cli.py`: CLI command execution
- Manual smoke test with real API

---

## Deployment (Future)

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

### Cloud Options
- **Heroku**: Simple deploy with Procfile
- **AWS Lambda**: Package as Docker image
- **Google Cloud Run**: Serverless containers
- **Fly.io**: Fast edge deployment

---

## Monitoring & Logging (Future)

### Metrics to Track
- API response times (LoopNet, OpenAI)
- Agent success/failure rates
- Score distributions
- User query patterns

### Tools
- **Sentry**: Error tracking
- **Datadog**: Performance monitoring
- **Loguru**: Structured logging

---

## FAQ

**Q: Why not use a database?**  
A: Keeping it simple for MVP. JSON files work fine for small-scale. Add PostgreSQL when needed.

**Q: Can I use other LLMs (Claude, Gemini)?**  
A: Yes! CrewAI supports multiple LLM providers. Update agent configuration.

**Q: How do I get location IDs for LoopNet?**  
A: Use LoopNet's search UI or their location lookup endpoint (not included in this project).

**Q: Why 1-100 instead of 1-10?**  
A: Higher granularity = better differentiation. Easy to convert (divide by 10).

**Q: Can agents call each other?**  
A: Not in this design (keep simple). Aggregator sees all outputs but doesn't delegate back.

---

## License

MIT - Use freely for personal or commercial projects.

---

**Built with ❤️ for real estate investors who want data-driven deal flow.**
