"""Construction scope and cost analyst."""
from crewai import Agent


def create_construction_agent() -> Agent:
    """
    Create Construction Scope & Cost analyst.
    
    Evaluates:
    - Likely scope level
    - Rough $/SF estimates
    - Timeline risks
    - Disruption risks
    """
    return Agent(
        role="Construction Scope & Cost Analyst",
        goal="Estimate renovation scope, costs, timeline, and disruption risks",
        backstory="""You are a construction and rehab specialist who quickly estimates 
        capital needs. From limited photos and property descriptions, you can gauge scope 
        level (light turn vs gut renovation), rough $/SF costs for the area and asset class, 
        timeline risks, and tenant disruption. You err on the conservative side and flag 
        major unknowns that require site inspection.""",
        verbose=False,
        allow_delegation=False,
    )


CONSTRUCTION_TASK_TEMPLATE = """
Estimate construction scope and costs for this property.

**Property Information:**
{property_info}

**Collaboration Context:** Other specialists will speak to investment metrics, neighborhood dynamics, and policy signals. Stay in your construction lane—diagnose scope, costs, and timeline risks. If data is missing, clearly state the site inspections or documents needed rather than repeating their insights.

**Your Task:**
1. Estimate likely scope level (light turn, moderate rehab, or gut renovation)
2. Rough $/SF cost band for the area/class (very rough estimate)
3. Timeline risk and disruption risk assessment
4. Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <integer 1-100, higher=lower scope risk/better capex outlook>,
  "rationale": "<2-3 sentence capex assessment>",
  "notes": [
    "<Estimated scope level: light/moderate/heavy>",
    "<Rough $/SF estimate or range>",
    "<Timeline risk assessment>",
    "<Disruption risk (tenant vacancy, income loss)>",
    "<Major unknowns requiring inspection>"
  ]
}}

**Scoring Guidelines:**
- 80-100: Minimal work needed, low capex, short timeline
- 60-79: Moderate work, manageable costs and timeline
- 40-59: Significant work, uncertain costs/timeline
- 20-39: Major renovation, high costs, long timeline
- 1-19: Severe issues, prohibitive costs or risks

Be conservative. Flag unknowns that could derail the project.
"""
