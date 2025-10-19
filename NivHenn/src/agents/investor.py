"""Investment analyst agent - long-term hold quality assessment."""
from crewai import Agent


def create_investor_agent() -> Agent:
    """
    Create Long-Term Investor agent.
    
    Evaluates:
    - Cash flow resilience
    - Downside protection
    - Tenant/demand quality
    - Exit liquidity
    """
    return Agent(
        role="Long-Term Investment Analyst",
        goal="Conservatively assess long-term hold quality and cash flow resilience",
        backstory="""You are a seasoned real estate investor focused on resilient cash flow 
        and downside protection. You prioritize sustainable tenant demand, conservative 
        underwriting, and clean exit strategies. You've weathered multiple market cycles 
        and know that conservative assumptions save fortunes.""",
        verbose=False,
        allow_delegation=False,
    )


INVESTOR_TASK_TEMPLATE = """
Analyze this commercial property listing for long-term investment quality.

**Listing Details:**
{listing_details}

**Your Task:**
1. Assess long-term hold quality (resilient cash flow, downside protection, tenant demand, exit liquidity)
2. Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <integer 1-100, higher=better>,
  "rationale": "<2-3 sentence explanation>",
  "notes": [
    "<key pro/con bullet 1>",
    "<key pro/con bullet 2>",
    "<key pro/con bullet 3>",
    "<underwriting assumption to test 1>",
    "<underwriting assumption to test 2>"
  ]
}}

**Scoring Guidelines:**
- 80-100: Exceptional quality, strong fundamentals, minimal risk
- 60-79: Good quality, solid fundamentals, manageable risk
- 40-59: Average quality, moderate concerns
- 20-39: Below average, significant concerns
- 1-19: Poor quality, major red flags

Be conservative and practical. Focus on what could go wrong and how to mitigate it.
"""
