"""Aggregator agent - synthesizes all specialist outputs into final memo."""
from crewai import Agent


def create_aggregator_agent() -> Agent:
    """
    Create Principal Investment Writer agent.
    
    Synthesizes all specialist agent outputs into:
    - Deal snapshot
    - Score table
    - Top risks & mitigations
    - Red flags
    - Investment thesis
    - Go/No-Go recommendation
    """
    return Agent(
        role="Principal Investment Writer",
        goal="Synthesize all analyses into a concise investment memo with clear go/no-go",
        backstory="""You are a principal investor who reviews all specialist analyses 
        and writes decisive investment memos. You combine quantitative scores with 
        qualitative insights to form a clear thesis. Your memos are concise (<= 1 page), 
        actionable, and include specific conditions for proceeding. You compute weighted 
        overall scores and explain the key drivers in 1-2 sentences.""",
        verbose=False,
        allow_delegation=False,
    )


AGGREGATOR_TASK_TEMPLATE = """
Synthesize all specialist analyses into a final investment memo.

**Property Summary:**
{property_summary}

**Specialist Scores:**
{specialist_scores}

**Specialist Rationales:**
{specialist_rationales}

**Your Task:**
Create a concise investment memo (<= 1 page) with these sections:
1. **Deal Snapshot**: Address, price, key specs (2-3 lines)
2. **Score Table**: List each specialist score (1-100) and overall weighted score
3. **Top 5 Risks & Mitigations**: Key concerns + how to address
4. **Red Flags**: Deal-breakers or critical unknowns
5. **Investment Thesis**: 3-4 sentence summary of the opportunity
6. **Go/No-Go**: Clear recommendation with conditions

**Weights for Overall Score:**
- Investment Analyst: 30%
- Location Risk: 25%
- VC Risk/Return: 20%
- Construction: 15%
- News Signals: 10%

Output EXACTLY in this JSON format (no extra text):
{{
  "score_1_to_100": <computed weighted overall score>,
  "rationale": "<1-2 sentence explanation of overall score drivers>",
  "notes": [
    "<memo in markdown format, ~1 page>",
    "<include all 6 sections mentioned above>",
    "<be decisive and concise>",
    "<format with markdown headers (##) and bullets>"
  ]
}}

The memo should be in notes[0] as a complete markdown document.
Be direct, actionable, and decisive.
"""
