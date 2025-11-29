# prompt.py
WEB_SEARCH_ANSWER_MAIN_INSTRUCTION = """
This is the main Web Search Answer Agent that orchestrates parallel retrieval across multiple queries.

The agent processes queries in parallel (ideally 9 queries from question generation) and for each query:
1. Executes web search (Google Search)
2. Executes Instagram search
3. Executes Twitter/X search
4. Synthesizes results into a final answer

Each query retrieval runs independently and in parallel for efficiency.

The agent coordinates the execution and aggregates all results.
"""

