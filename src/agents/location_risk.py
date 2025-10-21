"""Location and trajectory risk analyst."""
from crewai import Agent


def create_location_agent() -> Agent:
    """
    Create Location & Trajectory analyst.
    
    Evaluates:
    - Area trajectory (population, income trends)
    - Transit/walkability
    - Amenities and schools
    - Crime trends
    - Regulatory risks
    """
    return Agent(
        role="Location & Trajectory Analyst",
        goal="Evaluate area trajectory and near-term (2-5y) attractiveness",
        backstory="""You are a location intelligence specialist who predicts neighborhood 
        trajectories. You analyze demographics, transit access, local amenities, crime data, 
        and regulatory environments. You can spot early gentrification signals and identify 
        areas with hidden regulatory risks like rent control or eviction moratoria.""",
        verbose=False,
        allow_delegation=False,
    )


LOCATION_TASK_TEMPLATE = """
Analyze this property's location and trajectory.

**Location Details:**
{location_details}

**Collaboration Context:** Other teammates are covering investment fundamentals, construction, risk/return, and news. Deliver insights strictly about location trajectory and neighborhood texture. If information is sparse, call out location-specific data to gather rather than repeating general investment commentary.

**Your Task:**
1. Evaluate area trajectory using proxies: population/income trends, transit/walkability, 
   amenities/schools, crime trends, regulatory red flags
2. Predict near-term (2-5y) attractiveness and gentrification risk
3. Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <integer 1-100, higher=better trajectory>,
  "rationale": "<2-3 sentence assessment>",
  "notes": [
    "<population/income trend signal>",
    "<transit/walkability assessment>",
    "<amenities/schools vibe>",
    "<crime/safety trend>",
    "<regulatory risk or opportunity>"
  ]
}}

**Scoring Guidelines:**
- 80-100: Strong upward trajectory, minimal risks
- 60-79: Positive trajectory, some headwinds
- 40-59: Stable/flat, uncertain direction
- 20-39: Declining trajectory, significant concerns
- 1-19: Major decline or severe risks

Focus on concrete signals and be specific about risks to investigate further.
"""
