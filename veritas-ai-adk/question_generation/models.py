# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryItem(BaseModel):
    """A single search query with metadata."""
    qid: str = Field(..., description="Query identifier (e.g., q1, q2, q3)")
    query: str = Field(
        ...,
        description="Search-engine-friendly query string suitable for Google search. Use concrete terms, dates, quotes for exact phrases, and site: filters if provided."
    )
    notes: str = Field(
        ...,
        description="Brief explanation of why this query was generated and what it aims to verify"
    )


class Chain1Output(BaseModel):
    """Output schema for Chain 1: Direct verification queries."""
    chain: str = Field(default="1", description="Chain identifier")
    claim_id: Optional[str] = Field(None, description="Claim identifier from input")
    queries: List[QueryItem] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 queries for direct fact verification"
    )


class Chain2Output(BaseModel):
    """Output schema for Chain 2: Context follow-up queries."""
    chain: str = Field(default="2", description="Chain identifier")
    claim_id: Optional[str] = Field(None, description="Claim identifier from input")
    queries: List[QueryItem] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 queries for context and detail verification"
    )


class Chain3Output(BaseModel):
    """Output schema for Chain 3: Disambiguation queries."""
    chain: str = Field(default="3", description="Chain identifier")
    claim_id: Optional[str] = Field(None, description="Claim identifier from input")
    queries: List[QueryItem] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 queries for disambiguation and contradiction resolution"
    )


class QuestionGenerationInput(BaseModel):
    """Input schema for question generation agents."""
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The claim text to generate queries for")
    entities: Optional[List[str]] = Field(
        None,
        description="List of named entities (persons, organizations, locations) mentioned in the claim"
    )
    suggested_domains: Optional[List[str]] = Field(
        None,
        description="Recommended domains from severity source suggester (e.g., ['gov.in', 'rbi.org.in'])"
    )
    site_filters: Optional[str] = Field(
        None,
        description="Google search site: filters in format 'site:domain1.com OR site:domain2.com'"
    )
    language: Optional[str] = Field(default="en", description="Language code (e.g., 'en', 'hi')")
    # Note: doc_meta field removed to avoid additionalProperties in Gemini API schema


class Chain2Input(BaseModel):
    """Input schema for Chain 2 (includes Chain 1 results)."""
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The claim text")
    # Note: chain1_results field removed to avoid additionalProperties in Gemini API schema
    # Chain 1 results are available in state via output_key
    entities: Optional[List[str]] = Field(
        None,
        description="List of named entities"
    )
    suggested_domains: Optional[List[str]] = Field(
        None,
        description="Recommended domains"
    )
    language: Optional[str] = Field(default="en", description="Language code")


class Chain3Input(BaseModel):
    """Input schema for Chain 3 (includes Chain 1 and 2 results)."""
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The claim text")
    # Note: chain1_results and chain2_results fields removed to avoid additionalProperties in Gemini API schema
    # Chain results are available in state via output_key
    entities: Optional[List[str]] = Field(
        None,
        description="List of named entities"
    )
    language: Optional[str] = Field(default="en", description="Language code")

