# agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types

from .prompt import TWITTER_SEARCH_INSTRUCTION

# Create Twitter/X search agent using Google Search with site filter
# Uses Google Search with site:twitter.com to find Twitter/X content without API keys
twitter_search_agent = LlmAgent(
    name="twitter_search_agent",
    model="gemini-2.5-flash",
    description=(
        "Twitter/X search agent for retrieving evidence from tweets and threads. "
        "Uses Google Search with site:twitter.com filter to find relevant Twitter/X content, "
        "extracts tweet URLs, content, engagement metrics, and timestamps."
    ),
    instruction=TWITTER_SEARCH_INSTRUCTION,
    tools=[google_search],  # ADK built-in Google Search tool
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_key="twitter_search_results",
)

