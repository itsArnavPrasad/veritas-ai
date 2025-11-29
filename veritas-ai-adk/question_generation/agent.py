# agent.py
from google.adk.agents import SequentialAgent

# Import sub-agents
from .subagents.chain1.agent import chain1_agent
from .subagents.chain2.agent import chain2_agent
from .subagents.chain3.agent import chain3_agent

# Question Generation Agent (Sequential Orchestration)
question_generation_agent = SequentialAgent(
    name="question_generation_agent",
    description=(
        "Question Generation Agent: Generates investigative queries in three sequential chains for fact verification. "
        "Chain 1 produces 3 direct verification queries ('Did this event happen?'). "
        "Chain 2 produces 3 context/detail queries ('What are the details?'). "
        "Chain 3 produces 3 disambiguation queries ('Are there contradictions?'). "
        "Total: 9 queries (q1-q9) for comprehensive fact-checking retrieval."
    ),
    sub_agents=[
        chain1_agent,  # Chain 1: Direct verification (q1, q2, q3)
        chain2_agent,  # Chain 2: Context and details (q4, q5, q6)
        chain3_agent,  # Chain 3: Disambiguation (q7, q8, q9)
    ],
)

