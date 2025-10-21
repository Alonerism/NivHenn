# 🚀 Getting Started - Real Estate Scout

**5-Minute Quick Start Guide**

---

## ✅ Prerequisites

Before you begin, ensure you have:
- ✅ Python 3.11 or higher installed
- ✅ pip package manager
- ✅ RapidAPI account ([sign up](https://rapidapi.com/))
- ✅ OpenAI API key ([get key](https://platform.openai.com/api-keys))
- ✅ Serper API key (optional) for richer news insight ([claim a key](https://serper.dev))

Check your Python version:
```bash
python3 --version
# Should show: Python 3.11.x or higher
```

---

## 📥 Installation (2 Methods)

### Method 1: Automated Setup (Recommended)
```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

The script will:
1. ✅ Check Python version
2. ✅ Install dependencies
3. ✅ Create .env file
4. ✅ Run verification tests

### Method 2: Manual Setup
```bash
# Install dependencies
pip install -e .
# OR
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Verify installation
python verify_setup.py
```

---

## 🔑 Configure API Keys

Edit the `.env` file:
```bash
# Open in your favorite editor
nano .env
# or
code .env
# or
open .env
```

**Required keys** (replace with your actual keys):
```env
RAPIDAPI_KEY=your_rapidapi_key_here_not_SET_ME
OPENAI_API_KEY=sk-your_openai_key_here
```

**Optional keys**:
```env
SERPER_API_KEY=__OPTIONAL__
REDDIT_CLIENT_ID=__OPTIONAL__
REDDIT_CLIENT_SECRET=__OPTIONAL__
```

> ℹ️ If `SERPER_API_KEY` is missing the news agent automatically assigns a neutral 50± score and calls out the limitation.

### Where to Get Keys:

#### RapidAPI Key (LoopNet)
1. Go to https://rapidapi.com/
2. Sign up for a free account
3. Search for "LoopNet API"
4. Subscribe to a plan (free tier available)
5. Copy your API key from the dashboard

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. **Important**: Keep this key secure!

---

## ✅ Verify Setup

Run the verification script:
```bash
python verify_setup.py
```

**Expected output:**
```
====================================================
Real Estate Scout - Setup Verification
====================================================
Testing imports...
✓ httpx
✓ pydantic
✓ pydantic-settings
✓ tenacity
✓ crewai
✓ fastapi
✓ uvicorn
✓ python-dotenv
✓ rich

Testing configuration...
✓ Config loaded
✓ RAPIDAPI_KEY configured
✓ OPENAI_API_KEY configured
✓ Agent weights sum to 1.00

...

====================================================
SUMMARY
====================================================
Imports              ✓ PASS
Configuration        ✓ PASS
Models               ✓ PASS
Scoring              ✓ PASS
Agents               ✓ PASS
====================================================

✓ All checks passed! You're ready to run analysis.
```

**If you see errors:**
- Check that `.env` has valid API keys (not `__SET_ME__`)
- Run `pip install -e .` again
- See [SETUP.md](SETUP.md) Troubleshooting section

---

## 🎯 First Run - CLI Mode

### Simple Test (3 Properties)
```bash
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --size 3 \
  --price-min 500000 \
  --price-max 2000000
```

Want to reuse the stored filters instead? Run `python -m src.cli analyze --use-stored --size 3` (add `--persist-filters` to save overrides).

**What happens:**
1. Fetches 3 listings from LoopNet in Austin, TX (location ID 41096)
2. Runs 5 AI agents on each property
3. Calculates overall 1-100 scores
4. Displays results in a pretty table
5. Saves JSON + Markdown reports to `./out/`

**Expected runtime:** ~2-5 minutes (depending on OpenAI API speed)

### Review the Output

**Terminal Table:**
```
┌──────────────────────┬──────────┬────────┬──────────┬────────┐
│ Address              │ Ask      │ Invest │ Location │ Overall│
├──────────────────────┼──────────┼────────┼──────────┼────────┤
│ 123 Main St          │ $1.2M    │   78   │    82    │   76   │
└──────────────────────┴──────────┴────────┴──────────┴────────┘
```

**Files created in `./out/`:**
- `listing_<id>.json` - Full structured data
- `listing_<id>.md` - Investment memo (open this first!)

### Open a Report
```bash
# View the markdown memo
cat ./out/listing_*.md
# or open in VS Code
code ./out/
```

---

## 🌐 First Run - API Mode

### Start the Server
```bash
uvicorn src.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

### Access Interactive Docs
Open your browser and go to:
```
http://localhost:8000/docs
```

You'll see **Swagger UI** with interactive API documentation.

### Test the Health Endpoint
**In browser:** http://localhost:8000/health

**With curl:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "rapidapi_configured": true,
  "openai_configured": true,
  "weights": {
    "investment": 0.30,
    "location": 0.25,
    "vc_risk": 0.20,
    "construction": 0.15,
    "news": 0.10
  }
}
```

### Test Property Analysis
**In Swagger UI:**
1. Click on `POST /analyze`
2. Click "Try it out"
3. Paste this example request:
```json
{
  "locationId": "41096",
  "locationType": "city",
  "page": 1,
  "size": 3,
  "priceMin": 500000,
  "priceMax": 2000000
}
```
4. Click "Execute"
5. Review the JSON response

**With curl:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "locationId": "41096",
    "locationType": "city",
    "size": 3,
    "priceMin": 500000,
    "priceMax": 2000000
  }'
```

Skip the request body and reuse the saved filters:
```bash
curl -X POST "http://localhost:8000/analyze?use_stored=true"
```

### Manage Filters in Your Browser
- Visit `http://localhost:8000/filters/ui` for a no-build HTML editor with inline styling.
- The form writes to `config/filters.json`, which is also consumed by the CLI and API.
- Use the **Reset Defaults** button (or `POST /filters/reset`) to restore the starter configuration.

---

## 📖 Understanding the Scores

### Individual Agent Scores (1-100)

| Score Range | Meaning | Color |
|-------------|---------|-------|
| 80-100 | Exceptional - Strong buy | 🟢 Green |
| 60-79 | Good - Solid opportunity | 🟡 Yellow |
| 40-59 | Average - Neutral | ⚪ White |
| 20-39 | Below Average - Caution | 🟠 Orange |
| 1-19 | Poor - Avoid | 🔴 Red |

### Overall Score Calculation

**Formula:**
```
Overall = (Investment × 0.30) +
          (Location × 0.25) +
          (VC Risk × 0.20) +
          (Construction × 0.15) +
          (News × 0.10)
```

**Example:**
- Investment: 78 → 78 × 0.30 = 23.4
- Location: 82 → 82 × 0.25 = 20.5
- VC Risk: 70 → 70 × 0.20 = 14.0
- Construction: 75 → 75 × 0.15 = 11.25
- News: 65 → 65 × 0.10 = 6.5
- **Overall = 75.65 ≈ 76**

---

## 🎓 Next Steps

Now that you're set up, explore these options:

### 1. Try Different Locations
```bash
# Miami, FL (example location ID)
python -m src.cli analyze --location-id 29700 --size 5

# Los Angeles, CA (example location ID)
python -m src.cli analyze --location-id 41093 --size 5
```

**Note:** Location IDs are from LoopNet. You may need to look these up on the LoopNet website.

### 2. Customize Agent Weights
Edit `.env`:
```env
WEIGHT_INVESTMENT=0.35
WEIGHT_LOCATION=0.30
WEIGHT_VC_RISK=0.20
WEIGHT_CONSTRUCTION=0.10
WEIGHT_NEWS=0.05
```

### 3. Filter by Property Type
```bash
python -m src.cli analyze \
  --location-id 41096 \
  --property-type multifamily \
  --size 5
```

### 4. Read the Documentation
- **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - See workflow diagrams
- **[SETUP.md](SETUP.md)** - All CLI/API options
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works internally

### 5. Explore the Code
Start with these files:
- `src/main.py` - FastAPI application
- `src/cli.py` - CLI interface
- `src/app/crew.py` - Agent orchestration
- `src/agents/investor.py` - Example agent

---

## 🆘 Common Issues

### "Import could not be resolved"
**Solution:**
```bash
pip install -e .
```

### "RAPIDAPI_KEY not configured"
**Solution:**
1. Check that `.env` file exists
2. Open `.env` and replace `__SET_ME__` with your actual key
3. Restart the application

### "No listings found"
**Solution:**
- Try a different `location-id`
- Broaden your filters (remove `price-min`/`price-max`)
- Check that your RapidAPI subscription is active

### "Rate limit exceeded"
**Solution:**
- Wait a few minutes before trying again
- Reduce `--size` parameter
- Upgrade your RapidAPI plan

### Agent parsing errors
**This is normal!** Agents sometimes return non-JSON output. The system handles this gracefully by:
- Defaulting to a neutral score (50)
- Adding an error note
- Continuing with other agents

---

## 📚 Additional Resources

| Resource | Link | Purpose |
|----------|------|---------|
| **Full Setup Guide** | [SETUP.md](SETUP.md) | Detailed usage instructions |
| **Architecture Docs** | [ARCHITECTURE.md](ARCHITECTURE.md) | Technical design |
| **Visual Guide** | [VISUAL_GUIDE.md](VISUAL_GUIDE.md) | Diagrams and workflows |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs (when server running) |
| **Project Summary** | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete overview |
| **Docs Index** | [DOCS_INDEX.md](DOCS_INDEX.md) | Documentation navigation |

---

## ✅ Quick Reference

**Install:**
```bash
./setup.sh
```

**Verify:**
```bash
python verify_setup.py
```

**Run CLI:**
```bash
python -m src.cli analyze --location-id 41096 --size 3
```

**Start API:**
```bash
uvicorn src.main:app --reload
```

**Check Health:**
```bash
curl http://localhost:8000/health
```

---

## 🎉 You're Ready!

You've successfully set up the Real Estate Scout. Here's what to do next:

1. ✅ Run your first analysis with the CLI
2. ✅ Open the generated markdown memo in `./out/`
3. ✅ Experiment with different locations and filters
4. ✅ Try the API interface at http://localhost:8000/docs
5. ✅ Read the code to understand how it works

**Questions?** Check the troubleshooting section above or see [SETUP.md](SETUP.md).

**Happy scouting! 🏢📊🚀**
