# Setup Instructions

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Install the package in editable mode
pip install -e .

# Or install specific dependencies
pip install crewai httpx pydantic pydantic-settings tenacity fastapi uvicorn python-dotenv rich
```

### 2. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required keys in `.env`:
```bash
RAPIDAPI_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Getting API Keys:**
- **RapidAPI (LoopNet)**: Sign up at https://rapidapi.com/ and subscribe to LoopNet API
- **OpenAI**: Get your key at https://platform.openai.com/api-keys

### 3. Run Your First Analysis

```bash
# CLI mode
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --size 5 \
  --price-min 500000 \
  --price-max 3000000

# API mode
uvicorn src.main:app --reload
# Then visit http://localhost:8000/docs for interactive API docs
```

---

## CLI Usage

### Basic Command Structure

```bash
python -m src.cli analyze [OPTIONS]
```

### Common Examples

**1. Analyze 10 properties in Austin, TX**
```bash
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --size 10 \
  --price-min 500000 \
  --price-max 5000000
```

**2. Filter by building size**
```bash
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --building-size-min 5000 \
  --building-size-max 20000 \
  --size 5
```

**3. Custom output directory**
```bash
python -m src.cli analyze \
  --location-id 41096 \
  --location-type city \
  --size 5 \
  --output-dir ./my_analysis
```

### CLI Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--location-id` | LoopNet location ID (required) | - |
| `--location-type` | Type: city, state, zipcode | city |
| `--page` | Page number for pagination | 1 |
| `--size` | Number of results per page | 10 |
| `--price-min` | Minimum asking price | None |
| `--price-max` | Maximum asking price | None |
| `--building-size-min` | Min building size (SF) | None |
| `--building-size-max` | Max building size (SF) | None |
| `--property-type` | Property type filter | None |
| `--output-dir` | Output directory for reports | ./out |

---

## API Usage

### Start the Server

```bash
# Development mode (auto-reload)
uvicorn src.main:app --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Interactive API Docs

Visit http://localhost:8000/docs for Swagger UI with interactive API testing.

### API Endpoints

#### 1. Health Check
```bash
GET http://localhost:8000/health
```

Response:
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

#### 2. Analyze Properties
```bash
POST http://localhost:8000/analyze
Content-Type: application/json

{
  "locationId": "41096",
  "locationType": "city",
  "page": 1,
  "size": 5,
  "priceMin": 500000,
  "priceMax": 3000000
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "locationId": "41096",
    "locationType": "city",
    "size": 5,
    "priceMin": 500000,
    "priceMax": 3000000
  }'
```

**Example with Python:**
```python
import httpx

response = httpx.post(
    "http://localhost:8000/analyze",
    json={
        "locationId": "41096",
        "locationType": "city",
        "size": 5,
        "priceMin": 500000,
        "priceMax": 3000000
    }
)

reports = response.json()
for report in reports:
    print(f"{report['address']}: {report['scores']['overall']}/100")
```

---

## Understanding the Output

### CLI Output

1. **Terminal Table**: Compact view of all properties with scores
2. **JSON Files**: Full structured data in `./out/listing_<id>.json`
3. **Markdown Memos**: Human-readable analysis in `./out/listing_<id>.md`

### Score Interpretation

**Overall Score (1-100):**
- **80-100**: Strong buy candidate, minimal risks
- **60-79**: Good opportunity, manageable risks
- **40-59**: Neutral, requires deeper diligence
- **20-39**: Below average, significant concerns
- **1-19**: Avoid, major red flags

**Individual Agents:**
- **Investment Analyst (30%)**: Cash flow quality, downside protection
- **Location Risk (25%)**: Area trajectory, demographics
- **VC Risk/Return (20%)**: Risk mitigation strategies
- **Construction (15%)**: Capex estimates, timeline risks
- **News Signals (10%)**: Community sentiment, policy changes

---

## Troubleshooting

### "RAPIDAPI_KEY not configured"
- Ensure `.env` file exists in project root
- Check that `RAPIDAPI_KEY=your_actual_key` (not `__SET_ME__`)
- Restart the server/CLI after updating `.env`

### "Import could not be resolved" errors
- Run `pip install -e .` to install dependencies
- Ensure you're in a Python 3.11+ environment

### Rate limiting errors
- LoopNet API has rate limits on RapidAPI
- Wait a few minutes between large requests
- Consider upgrading your RapidAPI plan for higher limits

### Agent parsing errors
- CrewAI agents sometimes return non-JSON output
- The system has fallbacks to neutral scores (50)
- Check OpenAI API status if persistent

---

## Advanced Configuration

### Customize Agent Weights

Edit `.env`:
```bash
WEIGHT_INVESTMENT=0.35
WEIGHT_LOCATION=0.30
WEIGHT_VC_RISK=0.20
WEIGHT_CONSTRUCTION=0.10
WEIGHT_NEWS=0.05
```

### Add External Data Sources

Implement functions in `src/app/tools.py`:
- `geocode_address()`: Add geocoding API
- `search_news()`: Integrate News API
- `search_reddit()`: Connect to Reddit API
- `get_demographics()`: Use Census API

---

## Next Steps

1. **Run a test analysis** with a small area (size=3)
2. **Review the markdown memos** to understand agent reasoning
3. **Adjust weights** based on your investment priorities
4. **Integrate additional APIs** for richer data
5. **Build automations** around high-scoring deals

---

## Support

For issues or questions:
1. Check the main README.md
2. Review API docs at http://localhost:8000/docs
3. Check logs for detailed error messages

**Happy scouting! 🏢📊**
