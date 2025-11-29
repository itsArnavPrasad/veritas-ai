# agent.py
# Follow https://google.github.io/adk-docs/get-started/quickstart/ for setup details
from google.adk.agents import SequentialAgent

from .subagents.evidence_analyzer.agent import evidence_analyzer_agent
from .subagents.final_verifier.agent import final_verifier_agent

# Main verifier ensemble agent: Sequential pipeline of 2 merged agents
verifier_ensemble_agent = SequentialAgent(
    name="verifier_ensemble_agent",
    description=(
        "Verifier Ensemble Agent: Evaluates claims against retrieved evidence using multiple verification signals. "
        "Sequential execution: Evidence Analysis (NLI + Stance + Credibility + Temporal) → "
        "Final Verification (Score Combination + Aggregation)."
    ),
    sub_agents=[
        evidence_analyzer_agent,  # Step 1: Analyze all evidence items (NLI, stance, credibility, temporal)
        final_verifier_agent,     # Step 2: Combine scores and produce final verification output
    ],
)

