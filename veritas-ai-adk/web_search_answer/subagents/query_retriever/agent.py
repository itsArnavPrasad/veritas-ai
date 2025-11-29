# agent.py
from google.adk.agents import SequentialAgent

# Import sub-agents
from ..web_search.agent import web_search_agent
from ..instagram_search.agent import instagram_search_agent
from ..twitter_search.agent import twitter_search_agent
from ..answer_synthesis.agent import answer_synthesis_agent

# Create query retriever SequentialAgent
# This processes ONE query through the retrieval pipeline: web_search → instagram → twitter → synthesis
# When called as an AgentTool, the input (query_id, query_text, claim_id, etc.) is passed as the initial message
# to the first sub-agent (web_search_agent), which extracts the parameters from the input message
query_retriever_agent = SequentialAgent(
    name="query_retriever_agent",
    description=(
        "Query Retriever Agent: Executes sequential retrieval for a single query. "
        "Searches web (Google Search), Instagram, Twitter/X, then synthesizes results into a final answer. "
        "Input should contain query_id, query_text, claim_id (optional), site_filters (optional), recency_days (optional)."
    ),
    sub_agents=[
        web_search_agent,        # Step 1: Web search using Google Search (receives input and extracts parameters)
        instagram_search_agent,  # Step 2: Instagram search (receives query info from state/context)
        twitter_search_agent,    # Step 3: Twitter/X search (receives query info from state/context)
        answer_synthesis_agent,  # Step 4: Synthesize all results (combines evidence from all searches)
    ],
)

