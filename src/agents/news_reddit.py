"""News and community signals analyst."""
from crewai import Agent


def create_news_agent() -> Agent:
    """
    Create News & Community Signals analyst.
    
    Evaluates:
    - Zoning changes
    - Policy shifts
    - Notable incidents
    - Nuisance issues
    - Landlord-tenant friction
    """
    return Agent(
        role="News & Community Signals Analyst",
        goal="Detect policy shifts, incidents, and community sentiment from news/social data",
        backstory="""You are an investigative analyst who monitors news, social media, and 
        community forums for real estate signals. You track zoning changes, policy shifts, 
        notable incidents, nuisance issues, and landlord-tenant friction. You understand that 
        recent, severe, and frequent signals matter most. When data is unavailable, you 
        acknowledge it and score cautiously.""",
        verbose=False,
        allow_delegation=False,
    )


NEWS_TASK_TEMPLATE = """
Analyze news and community signals for this property's area.

**Area Information:**
{area_info}

**Available Data:**
{news_data}

**Collaboration Context:** Other analysts will comment on investment math, location fundamentals, and construction risk. Concentrate on policy, sentiment, and incident signals. Avoid restating broader investment or construction points—flag news gaps and community chatter that only you would notice.

**Your Task:**
1. Scan for: zoning changes, policy shifts, notable incidents, nuisance issues, 
   landlord-tenant friction
2. If no data available, acknowledge it and score conservatively
3. Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <integer 1-100, higher=fewer concerns>,
  "rationale": "<2-3 sentence assessment of signal quality>",
  "notes": [
    "<signal 1: [DATE] brief description>",
    "<signal 2: [DATE] brief description>",
    "<signal 3: if any, else 'No significant signals found'>",
    "<data limitation note if applicable>"
  ]
}}

**Scoring Guidelines:**
- 80-100: No significant negative signals, positive developments
- 60-79: Minor concerns, manageable issues
- 40-59: Moderate concerns or limited data (neutral)
- 20-39: Multiple concerning signals
- 1-19: Severe or frequent negative signals

Weight recent events more heavily. If no data available, default to 50 and note the limitation.
"""
