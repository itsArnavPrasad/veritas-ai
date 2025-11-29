# agent.py
# Follow https://google.github.io/adk-docs/get-started/quickstart/ for setup details
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent, Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from .models import WebSearchAnswerInput, WebSearchAnswerOutput
from .subagents.query_retriever.agent import query_retriever_agent

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# --- 1. Define Query Processor Sub-Agents (to run in parallel) ---
# Each agent processes one query (q1-q6) through the full retrieval pipeline:
# web_search → instagram_search → twitter_search → answer_synthesis

# Query Processor 1: Processes q1
query_processor_1 = LlmAgent(
    name="QueryProcessor1",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q1.

Your task: Extract query q1 from the input queries list and process it through the full retrieval pipeline.

The input will contain a list of queries (q1-q6). Extract ONLY query q1 (the query with qid="q1" or the first query).

Use the query_retriever_agent tool to process query q1. The tool will execute:
1. Web search (Google Search)
2. Instagram search
3. Twitter/X search
4. Answer synthesis

Input format: You will receive queries in a format like:
- queries: [{"qid": "q1", "query": "...", "notes": "..."}, ...]
- claim_id: The claim identifier

To process query q1:
1. Find the query with qid="q1" in the queries array
2. Call query_retriever_agent tool with a JSON string containing:
   {"query_id": "q1", "query_text": "[the query text from q1]", "claim_id": "[claim_id from input]"}

Format the tool call as: query_retriever_agent('{"query_id": "q1", "query_text": "...", "claim_id": "..."}')

Return the result from the query_retriever_agent tool. This will be the synthesized answer and evidence for query q1.
""",
    description="Processes query q1 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q1_result",
)

# Query Processor 2: Processes q2
query_processor_2 = LlmAgent(
    name="QueryProcessor2",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q2.

Extract query q2 (the query with qid="q2" or the second query) from the input queries list.
Call query_retriever_agent tool with a JSON string: {"query_id": "q2", "query_text": "[query text from q2]", "claim_id": "[claim_id]"}

Return the result from query_retriever_agent. This processes q2 through web search, Instagram search, Twitter search, and synthesis.
""",
    description="Processes query q2 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q2_result",
)

# Query Processor 3: Processes q3
query_processor_3 = LlmAgent(
    name="QueryProcessor3",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q3.

Extract query q3 (the query with qid="q3" or the third query) from the input queries list.
Call query_retriever_agent tool with a JSON string: {"query_id": "q3", "query_text": "[query text from q3]", "claim_id": "[claim_id]"}

Return the result from query_retriever_agent. This processes q3 through web search, Instagram search, Twitter search, and synthesis.
""",
    description="Processes query q3 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q3_result",
)

# Query Processor 4: Processes q4
query_processor_4 = LlmAgent(
    name="QueryProcessor4",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q4.

Extract query q4 (the query with qid="q4" or the fourth query) from the input queries list.
Call query_retriever_agent tool with a JSON string: {"query_id": "q4", "query_text": "[query text from q4]", "claim_id": "[claim_id]"}

Return the result from query_retriever_agent. This processes q4 through web search, Instagram search, Twitter search, and synthesis.
""",
    description="Processes query q4 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q4_result",
)

# Query Processor 5: Processes q5
query_processor_5 = LlmAgent(
    name="QueryProcessor5",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q5.

Extract query q5 (the query with qid="q5" or the fifth query) from the input queries list.
Call query_retriever_agent tool with a JSON string: {"query_id": "q5", "query_text": "[query text from q5]", "claim_id": "[claim_id]"}

Return the result from query_retriever_agent. This processes q5 through web search, Instagram search, Twitter search, and synthesis.
""",
    description="Processes query q5 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q5_result",
)

# Query Processor 6: Processes q6
query_processor_6 = LlmAgent(
    name="QueryProcessor6",
    model=GEMINI_MODEL,
    instruction="""You are a fact-checking query processor specialized for query q6.

Extract query q6 (the query with qid="q6" or the sixth query) from the input queries list.
Call query_retriever_agent tool with a JSON string: {"query_id": "q6", "query_text": "[query text from q6]", "claim_id": "[claim_id]"}

Return the result from query_retriever_agent. This processes q6 through web search, Instagram search, Twitter search, and synthesis.
""",
    description="Processes query q6 through web search, Instagram search, Twitter search, and synthesis.",
    tools=[AgentTool(agent=query_retriever_agent)],
    output_key="query_q6_result",
)


# --- 2. Create the ParallelAgent (Runs query processors concurrently) ---
# This agent orchestrates the concurrent execution of all 6 query processors.
# Each processor runs independently and outputs its result using output_key.
parallel_query_processor = ParallelAgent(
    name="ParallelQueryProcessor",
    sub_agents=[
        query_processor_1,
        query_processor_2,
        query_processor_3,
        query_processor_4,
        query_processor_5,
        query_processor_6,
    ],
    description="Runs 6 query processor agents in parallel to gather evidence for fact-checking queries.",
)

# --- 3. Define the Merger/Synthesis Agent (Runs *after* the parallel agents) ---
# This agent takes the results from the parallel agents (stored via output_key) and synthesizes them.
merger_agent = LlmAgent(
    name="EvidenceSynthesisAgent",
    model=GEMINI_MODEL,
    instruction="""You are an AI Assistant responsible for combining fact-checking evidence from 6 parallel queries into a structured format.

**IMPORTANT - Accessing Results:**
Since you are part of a SequentialAgent that runs after a ParallelAgent, the results from all 6 query processors are stored in session state with these keys:
- query_q1_result
- query_q2_result
- query_q3_result
- query_q4_result
- query_q5_result
- query_q6_result

Access these results from session state. Each result contains a SynthesizedAnswer with evidence items.

**Your task:**
1. Access results from all 6 query processors (q1-q6) from session state
2. Extract ALL evidence items from each query result (from the query_retriever_agent outputs)
3. Combine all evidence items into a structured format matching WebSearchAnswerOutput schema:
   - claim_id: Extract from input
   - query_results: List of QueryRetrievalOutput (one per query q1-q6)
     * Each QueryRetrievalOutput should contain: query_id, evidence_items list, total_results
   - total_evidence_items: Sum of all evidence items across all queries
   - retrieval_version: "web-search-answer-v1.0"

**IMPORTANT**: Preserve all evidence items from all 6 queries. Each query's evidence_items should contain the original evidence from web search, Instagram, and Twitter.

Output structured JSON matching WebSearchAnswerOutput schema. Do NOT lose any evidence items - include all evidence from all 6 queries.
""",
    description="Combines evidence from 6 parallel query processors into WebSearchAnswerOutput format with all evidence items preserved.",
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=WebSearchAnswerOutput,
    output_key="web_search_results",
)

# --- 4. Create the SequentialAgent (Orchestrates the overall flow) ---
# This agent orchestrates parallel query processing and evidence synthesis
# It first executes the ParallelAgent to populate the state, and then executes the MergerAgent to produce the final output.
web_search_answer_agent = SequentialAgent(
    name="WebSearchAnswerPipeline",
    # Run parallel query processing first, then merge
    sub_agents=[parallel_query_processor, merger_agent],
    description="Coordinates parallel fact-checking query processing across 6 queries and synthesizes the results.",
)

