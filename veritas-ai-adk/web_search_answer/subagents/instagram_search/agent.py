# agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types

from .prompt import INSTAGRAM_SEARCH_INSTRUCTION

# Create Instagram search agent using Google Search with site filter
# Uses Google Search with site:instagram.com to find Instagram content without API keys
instagram_search_agent = LlmAgent(
    name="instagram_search_agent",
    model="gemini-2.5-flash",
    description=(
        "Instagram search agent for retrieving evidence from Instagram posts, reels, and stories. "
        "Uses Google Search with site:instagram.com filter to find relevant Instagram content, "
        "extracts post URLs, captions, engagement metrics, and timestamps."
    ),
    instruction=INSTAGRAM_SEARCH_INSTRUCTION,
    tools=[google_search],  # ADK built-in Google Search tool
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_key="instagram_search_results",
)

