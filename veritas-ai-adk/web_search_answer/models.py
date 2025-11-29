# models.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime
import uuid


class SocialMetrics(BaseModel):
    """Social media engagement metrics."""
    platform: str = Field(..., description="Platform name: x, instagram, twitter, reddit, tiktok, etc.")
    likes: Optional[int] = Field(None, description="Number of likes/upvotes")
    retweets: Optional[int] = Field(None, description="Number of retweets/shares")
    replies: Optional[int] = Field(None, description="Number of replies/comments")
    views: Optional[int] = Field(None, description="Number of views")
    followers: Optional[int] = Field(None, description="Author follower count")
    # Note: extra field removed to avoid additionalProperties in Gemini API schema


class AdditionalMeta(BaseModel):
    """Additional metadata for evidence items."""
    social_metrics: Optional[SocialMetrics] = Field(None, description="Social media metrics if from social platform")
    author: Optional[str] = Field(None, description="Author name")
    sourced_by: Optional[str] = Field(None, description="Social source identifier, e.g., 'twitter:user123'")
    snapshot: Optional[str] = Field(None, description="S3/GCS path to saved HTML/screenshot snapshot")
    fact_check_rating: Optional[str] = Field(None, description="Fact-check rating if from fact-check site")
    verification_status: Optional[str] = Field(None, description="Verification status from platform")
    # Note: extra field removed to avoid additionalProperties in Gemini API schema


class EvidenceItem(BaseModel):
    """A single evidence item retrieved from a search."""
    evidence_id: str = Field(default_factory=lambda: f"e-{uuid.uuid4().hex[:8]}", description="Unique evidence identifier")
    query_id: str = Field(..., description="Query identifier (e.g., q1, q2, q3)")
    retriever: str = Field(..., description="Retriever name: google_search, instagram_search, twitter_search, bm25, dense, reverse_claim, etc.")
    url: Optional[HttpUrl] = Field(None, description="URL of the evidence source")
    title: Optional[str] = Field(None, description="Title of the evidence/article")
    snippet: str = Field(..., description="Extracted passage/snippet relevant to the query")
    full_text: Optional[str] = Field(None, description="Optional full text of the document")
    published_at: Optional[str] = Field(None, description="ISO-8601 datetime string of publication date")
    domain: Optional[str] = Field(None, description="Domain name (e.g., 'example.com')")
    retriever_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Retriever confidence/relevance score [0-1]")
    additional_meta: Optional[AdditionalMeta] = Field(None, description="Additional metadata")
    # Note: raw_tool_response field removed to avoid additionalProperties in Gemini API schema
    fetch_time: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="ISO-8601 timestamp when evidence was fetched")


class QueryRetrievalInput(BaseModel):
    """Input for a single query retrieval."""
    query_id: str = Field(..., description="Query identifier (e.g., q1)")
    query_text: str = Field(..., description="The search query text")
    claim_id: Optional[str] = Field(None, description="Claim identifier")
    site_filters: Optional[str] = Field(None, description="Google search site: filters")
    recency_days: Optional[int] = Field(None, description="Filter results to last N days")
    # Note: search_params field removed to avoid additionalProperties in Gemini API schema


class QueryRetrievalOutput(BaseModel):
    """Output for a single query retrieval (contains all evidence from all retrievers)."""
    query_id: str = Field(..., description="Query identifier")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="List of evidence items from all retrievers")
    retrieval_summary: Optional[str] = Field(None, description="Summary of retrieval results")
    total_results: int = Field(default=0, description="Total number of evidence items retrieved")


class QueryItem(BaseModel):
    """A single query item."""
    qid: str = Field(..., description="Query identifier (e.g., q1, q2, q3)")
    query: str = Field(..., description="The search query text")
    notes: Optional[str] = Field(None, description="Optional notes about the query")


class WebSearchAnswerInput(BaseModel):
    """Input for the main web search answer agent."""
    claim_id: str = Field(..., description="Claim identifier")
    queries: List[QueryItem] = Field(..., description="List of queries with qid and query text, from question generation")
    # Note: search_params field removed to avoid additionalProperties in Gemini API schema
    claim_text: Optional[str] = Field(None, description="Original claim text for context")


class WebSearchAnswerOutput(BaseModel):
    """Output from the main web search answer agent."""
    claim_id: str = Field(..., description="Claim identifier")
    query_results: List[QueryRetrievalOutput] = Field(..., description="Results for each query")
    total_evidence_items: int = Field(default=0, description="Total evidence items across all queries")
    retrieval_version: str = Field(default="web-search-answer-v1.0", description="Agent version identifier")
    comprehensive_answer: Optional[str] = Field(None, description="Comprehensive synthesized answer from all queries (added by comprehensive_answer_synthesis_agent)")


class SynthesizedAnswer(BaseModel):
    """Synthesized answer from multiple evidence sources."""
    query_id: str = Field(..., description="Query identifier")
    synthesized_text: str = Field(..., description="Synthesized answer combining evidence from all sources")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Evidence IDs that support this answer")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score [0-1]")
    synthesis_notes: Optional[str] = Field(None, description="Notes about the synthesis process")

