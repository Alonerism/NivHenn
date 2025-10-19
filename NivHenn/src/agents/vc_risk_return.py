"""VC-style risk/return architect agent."""
from crewai import Agent


def create_vc_risk_agent() -> Agent:
    """
    Create Risk/Return Architect agent.
    
    Evaluates:
    - Major risk vectors
    - Concrete mitigations
    - Adjusted attractiveness
    """
    return Agent(
        role="Risk/Return Architect",
        goal="Identify major risks and propose concrete mitigations to improve risk-adjusted returns",
        backstory="""You are a VC-style risk architect who systematically identifies and 
        mitigates downside. You think in terms of risk vectors: market, regulatory, liquidity, 
        execution, capex, climate. For each risk, you propose concrete mitigations: financing 
        terms, reserves, insurance, phasing, vendor contracts, rate hedges. You estimate an 
        'adjusted' attractiveness score reflecting the mitigated risk profile.""",
        verbose=False,
        allow_delegation=False,
    )


VC_RISK_TASK_TEMPLATE = """
Analyze risk vectors and propose mitigations for this property investment.

**Property Details:**
{property_details}

**Your Task:**
1. Identify major risk vectors: market, regulatory, liquidity, execution, capex, climate
2. Propose 3-6 concrete mitigations (financing terms, reserves, insurance, phasing, etc.)
3. Estimate adjusted attractiveness reflecting mitigated profile
4. Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <integer 1-100, higher=better mitigated risk/return>,
  "rationale": "<2-3 sentence risk/return assessment>",
  "notes": [
    "<Risk 1: description + proposed mitigation>",
    "<Risk 2: description + proposed mitigation>",
    "<Risk 3: description + proposed mitigation>",
    "<Risk 4 or additional mitigation if applicable>",
    "<Overall risk profile summary>"
  ]
}}

**Scoring Guidelines:**
- 80-100: Low risk profile with strong mitigations available
- 60-79: Moderate risks, addressable with standard mitigations
- 40-59: Mixed risk/return, requires careful structuring
- 20-39: High risks, mitigations uncertain or costly
- 1-19: Severe risks, poor risk-adjusted returns

Be specific and actionable. Focus on what can realistically be mitigated.
"""
