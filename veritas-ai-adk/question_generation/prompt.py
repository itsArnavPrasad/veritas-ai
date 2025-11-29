# prompt.py
# This file can contain shared prompt utilities or be left empty if prompts are only in sub-agents
# Main orchestration prompt is not needed for SequentialAgent - it runs sub-agents in sequence automatically

QUESTION_GENERATION_MAIN_INSTRUCTION = """
This is the main Question Generation Agent that orchestrates three sequential chains of question generation.

The agent executes three sub-agents in sequence:
1. Chain 1: Direct verification queries (3 queries)
2. Chain 2: Context and detail queries (3 queries)
3. Chain 3: Disambiguation queries (3 queries)

Total: 9 queries generated across the three chains.

Each chain agent generates its queries based on the claim and previous chain results.
"""

