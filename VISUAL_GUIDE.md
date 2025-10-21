# 🎨 Real Estate Scout - Visual Guide

## 🔄 Complete Workflow

```
┌─────────────┐
│    USER     │
│  (You!)     │
└──────┬──────┘
       │
       ├─── Option 1: CLI ────────────────┐
       │                                  │
       │    python -m src.cli analyze     │
       │    --location-id 41096           │
       │    --size 5                      │
       │    --price-min 500000            │
       │                                  │
       └─── Option 2: API ────────────────┤
                                           │
            POST /analyze                  │
            { "locationId": "41096",       │
              "size": 5 }                  │
                                           │
       ┌───────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│  LoopNet Client  │──────► RapidAPI LoopNet
│  (HTTPX+Retry)   │        (Commercial RE Data)
└────────┬─────────┘
         │
         ▼
    [Listings]
         │
    ┌────┴────┐
    │ For each│
    │ listing │
    └────┬────┘
         │
         ▼
┌─────────────────────────────────────┐
│     PropertyAnalysisCrew            │
│     (CrewAI Orchestrator)           │
└───────────┬─────────────────────────┘
            │
            ├──► Investment Analyst (30%)
            │    ├─ Cash flow quality
            │    ├─ Downside protection
            │    └─ Exit liquidity
            │
            ├──► Location Risk (25%)
            │    ├─ Demographics
            │    ├─ Transit/walkability
            │    └─ Regulatory risks
            │
            ├──► News Signals (10%)
            │    ├─ Policy changes
            │    ├─ Community sentiment
            │    └─ Incidents
            │
            ├──► VC Risk/Return (20%)
            │    ├─ Risk vectors
            │    ├─ Mitigations
            │    └─ Adjusted score
            │
            └──► Construction (15%)
                 ├─ Scope estimate
                 ├─ Cost bands
                 └─ Timeline risks
                 │
                 ▼
            Each returns:
            {
              score_1_to_100: 75,
              rationale: "...",
              notes: [...]
            }
                 │
                 ▼
         ┌───────────────┐
         │  Compute      │
         │  Weighted     │
         │  Overall      │
         │  Score        │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │  Aggregator   │
         │  Agent        │
         │  (Memo        │
         │   Writer)     │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │  FinalReport  │
         │  ============ │
         │  • Scores     │
         │  • Memo (MD)  │
         │  • Raw Data   │
         └───────┬───────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
  ┌─────────┐      ┌──────────┐
  │ Console │      │   Files  │
  │  Table  │      │  ./out/  │
  │ (Rich)  │      │ JSON+MD  │
  └─────────┘      └──────────┘
```

---

## 📊 Agent Scoring System

```
Property: 123 Main St, Austin, TX
Ask Price: $1,200,000
─────────────────────────────────────────

┌─────────────────────────┬───────┬────────┐
│ Agent                   │ Score │ Weight │
├─────────────────────────┼───────┼────────┤
│ Investment Analyst      │  78   │  30%   │
│ Location Risk           │  82   │  25%   │
│ VC Risk/Return          │  70   │  20%   │
│ Construction            │  75   │  15%   │
│ News Signals            │  65   │  10%   │
├─────────────────────────┼───────┼────────┤
│ OVERALL SCORE           │  76   │ 100%   │
└─────────────────────────┴───────┴────────┘

Calculation:
Overall = (78×0.30) + (82×0.25) + (70×0.20) + (75×0.15) + (65×0.10)
        = 23.4 + 20.5 + 14.0 + 11.25 + 6.5
        = 75.65 ≈ 76
```

---

## 🎯 Score Interpretation Guide

```
┌────────────┬──────────────────────────────────────────┐
│  Score     │  Meaning                                 │
├────────────┼──────────────────────────────────────────┤
│  90-100    │  🟢 EXCEPTIONAL - Strong buy candidate   |
│            │     Minimal risks, excellent fundamentals│
├────────────┼──────────────────────────────────────────┤
│  80-89     │  🟢 EXCELLENT - Great opportunity        │
│            │     Strong metrics, manageable risks     │
├────────────┼──────────────────────────────────────────┤
│  70-79     │  🟡 GOOD - Solid opportunity             │
│            │     Good fundamentals, some headwinds    │
├────────────┼──────────────────────────────────────────┤
│  60-69     │  🟡 FAIR - Worth deeper diligence        │
│            │     Mixed signals, requires analysis     │
├────────────┼──────────────────────────────────────────┤
│  50-59     │  ⚪ NEUTRAL - Uncertain                   │
│            │     Limited data or unclear signals      │
├────────────┼──────────────────────────────────────────┤
│  40-49     │  🟠 BELOW AVERAGE - Caution advised      │
│            │     Multiple concerns identified         │
├────────────┼──────────────────────────────────────────┤
│  30-39     │  🟠 POOR - Significant risks             │
│            │     Major concerns, risky investment     │
├────────────┼──────────────────────────────────────────┤
│  1-29      │  🔴 AVOID - Critical red flags           │
│            │     Deal-breakers present, do not pursue │
└────────────┴──────────────────────────────────────────┘
```

---

## 🗂️ File Structure Visualization

```
real-estate-scout/
│
├── 📋 Configuration Files
│   ├── .env.example          ← Template (copy to .env)
│   ├── .gitignore            ← Git ignore rules
│   ├── pyproject.toml        ← Package config
│   └── requirements.txt      ← Dependencies
│
├── 📖 Documentation
│   ├── README.md             ← Start here!
│   ├── SETUP.md              ← Setup instructions
│   ├── ARCHITECTURE.md       ← Technical design
│   ├── PROJECT_SUMMARY.md    ← Complete overview
│   └── VISUAL_GUIDE.md       ← This file!
│
├── 🛠️ Setup Tools
│   ├── setup.sh              ← Quick setup script (./setup.sh)
│   └── verify_setup.py       ← Verify installation
│
├── 📁 src/
│   ├── 🎛️ Entry Points
│   │   ├── __main__.py       ← CLI entry (python -m src.cli)
│   │   ├── cli.py            ← CLI interface (Rich)
│   │   └── main.py           ← FastAPI app (uvicorn src.main:app)
│   │
│   ├── 🏗️ app/ (Core Logic)
│   │   ├── config.py         ← Settings (env vars)
│   │   ├── models.py         ← Pydantic schemas
│   │   ├── loopnet_client.py ← API client (HTTPX)
│   │   ├── crew.py           ← CrewAI orchestration
│   │   ├── scoring.py        ← Score calculations
│   │   └── tools.py          ← Helper functions
│   │
│   └── 🤖 agents/ (AI Specialists)
│       ├── investor.py       ← Investment analyst
│       ├── location_risk.py  ← Location trajectory
│       ├── news_reddit.py    ← News signals
│       ├── vc_risk_return.py ← Risk/return
│       ├── construction.py   ← Construction scope
│       └── aggregator.py     ← Final memo writer
│
└── 📂 out/                   ← Generated reports
    ├── listing_12345.json    ← Structured data
    └── listing_12345.md      ← Investment memo
```

---

## 🔧 CLI Command Breakdown

```bash
python -m src.cli analyze \
  --location-id 41096 \        # LoopNet location ID (required)
  --location-type city \        # Type: city/state/zipcode
  --size 5 \                    # Number of listings to fetch
  --price-min 500000 \          # Minimum asking price
  --price-max 3000000 \         # Maximum asking price
  --building-size-min 5000 \    # Min square feet (optional)
  --building-size-max 20000 \   # Max square feet (optional)
  --property-type multifamily \ # Filter by type (optional)
  --output-dir ./my_reports     # Where to save results
```

**Output:**
```
Real Estate Scout - Property Analysis
=====================================

Search Parameters:
  Location: 41096 (city)
  Price Range: $500,000 - $3,000,000
  Results: 5 listings

Step 1: Fetching listings from LoopNet...
✓ Found 5 listings

Step 2: Running multi-agent analysis...
[████████████████████] 5/5

✓ Analysis complete!

┌──────────────────────┬──────────┬────────┬──────────┬────────┐
│ Address              │ Ask      │ Invest │ Location │ Overall│
├──────────────────────┼──────────┼────────┼──────────┼────────┤
│ 123 Main St          │ $1.2M    │   78   │    82    │   76   │
│ 456 Oak Ave          │ $2.5M    │   85   │    88    │   82   │
└──────────────────────┴──────────┴────────┴──────────┴────────┘

Step 3: Saving reports...
✓ Saved listing_12345.json and listing_12345.md
✓ Saved listing_67890.json and listing_67890.md

✓ All done! Reports saved to ./out/
```

---

## 🌐 API Usage Visualization

```
┌──────────────┐
│  Your App    │
└──────┬───────┘
       │
       │ POST http://localhost:8000/analyze
       │ Content-Type: application/json
       │
       │ {
       │   "locationId": "41096",
       │   "locationType": "city",
       │   "page": 1,
       │   "size": 5,
       │   "priceMin": 500000,
       │   "priceMax": 3000000
       │ }
       │
       ▼
┌──────────────────┐
│  FastAPI Server  │
│  (src/main.py)   │
└──────┬───────────┘
       │
       │ 1. Validate request (Pydantic)
       │ 2. Fetch from LoopNet
       │ 3. Run multi-agent analysis
       │ 4. Return results
       │
       ▼
┌──────────────────┐
│  JSON Response   │
└──────────────────┘

[
  {
    "listing_id": "12345",
    "address": "123 Main St, Austin, TX",
    "ask_price": 1200000,
    "scores": {
      "investment": 78,
      "location": 82,
      "news_signal": 65,
      "risk_return": 70,
      "construction": 75,
      "overall": 76
    },
    "memo_markdown": "## Deal Snapshot\n..."
  },
  ...
]
```

---

## 🎓 Learning Path

```
1. START HERE
   ├─► Read README.md (5 min)
   └─► Run setup.sh (5 min)

2. FIRST RUN
   ├─► Add API keys to .env
   ├─► Run verify_setup.py
   └─► Test with: python -m src.cli analyze --location-id 41096 --size 3

3. UNDERSTAND OUTPUT
   ├─► Review terminal table
   ├─► Open ./out/listing_xxx.md
   └─► Read the markdown memo

4. EXPLORE CODE
   ├─► Start: src/main.py or src/cli.py
   ├─► Core: src/app/crew.py
   ├─► Agents: src/agents/investor.py
   └─► Scoring: src/app/scoring.py

5. CUSTOMIZE
   ├─► Adjust weights in .env
   ├─► Modify agent prompts
   ├─► Add new agents (copy existing)
   └─► Integrate external APIs (tools.py)

6. EXTEND
   ├─► Add more filters
   ├─► Build frontend
   ├─► Deploy to cloud
   └─► Add database for history
```

---

## 🚦 Health Check Flow

```bash
# Check API status
curl http://localhost:8000/health
```

```
Response:
{
  "status": "healthy",
  "rapidapi_configured": true,   ← ✓ Key is set
  "openai_configured": true,     ← ✓ Key is set
  "weights": {                   ← Current agent weights
    "investment": 0.30,
    "location": 0.25,
    "vc_risk": 0.20,
    "construction": 0.15,
    "news": 0.10
  }
}
```

---

## 💾 Output Files Example

### 📄 listing_12345.json (Structured Data)
```json
{
  "listing_id": "12345",
  "address": "123 Main St, Austin, TX 78701",
  "ask_price": 1200000,
  "scores": {
    "investment": 78,
    "location": 82,
    "news_signal": 65,
    "risk_return": 70,
    "construction": 75,
    "overall": 76
  },
  "memo_markdown": "## Deal Snapshot\n...",
  "investment_output": {
    "score_1_to_100": 78,
    "rationale": "Solid cash flow fundamentals...",
    "notes": ["Pro: Strong tenant demand", "Con: Higher OpEx"]
  }
  ...
}
```

### 📝 listing_12345.md (Human-Readable Memo)
```markdown
# Property Analysis: 123 Main St, Austin, TX

**Ask Price:** $1,200,000
**Overall Score:** 76/100

---

## Deal Snapshot
Multi-family property in growing Austin submarket...

## Score Table
- Investment Analyst: 78/100
- Location Risk: 82/100
- VC Risk/Return: 70/100
- Construction: 75/100
- News Signals: 65/100

## Top 5 Risks & Mitigations
1. Rising OpEx → Implement energy efficiency upgrades
2. Market saturation → Target niche demographics
...

## Investment Thesis
Strong fundamentals with manageable risks. Location
trajectory is positive...

## Go/No-Go
**GO** - Proceed with LOI contingent on full due diligence
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| **Install** | `./setup.sh` or `pip install -e .` |
| **Verify** | `python verify_setup.py` |
| **CLI Run** | `python -m src.cli analyze --location-id 41096 --size 5` |
| **API Start** | `uvicorn src.main:app --reload` |
| **API Docs** | Visit `http://localhost:8000/docs` |
| **Check Health** | `curl http://localhost:8000/health` |

---

## 🆘 Troubleshooting

```
Problem: ImportError
Solution: pip install -e .

Problem: "RAPIDAPI_KEY not set"
Solution: Edit .env file, add RAPIDAPI_KEY=your_key

Problem: Agent parsing errors
Solution: Normal! System defaults to score 50 on failures

Problem: Rate limiting
Solution: Wait a few minutes or upgrade RapidAPI plan

Problem: No listings found
Solution: Try different location-id or broader filters
```

---

**🎉 You're ready to go! Start with `./setup.sh` and happy scouting! 🏢**
