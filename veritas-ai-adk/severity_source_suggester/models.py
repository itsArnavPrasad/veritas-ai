# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SeverityInfo(BaseModel):
    """Severity classification for a claim."""
    category: str = Field(
        ...,
        description="One of: political, health, finance, public_safety, social_emotional, technology, education, other",
        example="political"
    )
    severity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Severity score [0-1] indicating potential harm or sensitivity"
    )
    sensitivity_flags: Optional[List[str]] = Field(
        None,
        description="List of sensitivity indicators like 'election', 'public_official', 'medical_claim', 'financial_regulation', etc.",
        example=["election", "public_official"]
    )


class SourcePool(BaseModel):
    """A recommended source pool with prioritized domains."""
    pool_name: str = Field(
        ...,
        description="Name of the source pool: official_gov, top_global_media, indian_factchecks, health_orgs, finance_media, etc.",
        example="official_gov"
    )
    domains: List[str] = Field(
        ...,
        description="List of domain names (without protocol) for this source pool",
        example=["gov.in", "rbi.org.in"]
    )
    priority: int = Field(
        ...,
        ge=1,
        description="Priority level (1=highest priority, 2=secondary, 3=tertiary)",
        example=1
    )


class SeveritySourceSuggestionInput(BaseModel):
    """Input schema for the severity source suggester agent."""
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The claim text to analyze")
    entities: Optional[List[str]] = Field(
        None,
        description="List of named entities (persons, organizations, locations) mentioned in the claim"
    )
    # Note: doc_meta field removed to avoid additionalProperties in Gemini API schema
    # Document metadata can be passed as individual fields if needed
    claim_type: Optional[List[str]] = Field(
        None,
        description="Claim types from claim extractor (policy, temporal, geographic, etc.)"
    )


class SeveritySourceSuggestionOutput(BaseModel):
    """Output schema for the severity source suggester agent."""
    claim_id: str = Field(..., description="Unique claim identifier")
    severity: SeverityInfo = Field(..., description="Severity classification")
    recommended_source_pools: List[SourcePool] = Field(
        ...,
        description="Prioritized list of trusted source pools with domain recommendations"
    )
    social_platforms: List[str] = Field(
        ...,
        description="Recommended social platforms to check for rumor spread: x, reddit, instagram, tiktok, telegram, facebook, etc."
    )
    explainable_reasoning: str = Field(
        ...,
        description="Human-readable explanation of why these sources and platforms were selected"
    )
    site_filters: Optional[str] = Field(
        None,
        description="Google search site: filters in format suitable for queries, e.g., 'site:gov.in OR site:rbi.org.in'"
    )
    suggester_version: str = Field(
        default="suggester-v1.0",
        description="Agent version identifier"
    )
    # Note: extras field removed to avoid additionalProperties in Gemini API schema

