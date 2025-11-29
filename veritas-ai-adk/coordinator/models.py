# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class FactCheckingPipelineInput(BaseModel):
    """Input schema for the fact-checking pipeline coordinator."""
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    source: str = Field(..., description="Input source type: 'url' or 'text_upload'")
    url: Optional[str] = Field(None, description="URL if source is 'url'")
    raw_text: Optional[str] = Field(None, description="Raw text if source is 'text_upload'")
    html_snippet: Optional[str] = Field(None, description="HTML content if available")
    fetch_snapshot: bool = Field(default=False, description="Whether to fetch snapshots")
    additional_notes: Optional[str] = Field(None, description="Additional context or notes")


class FactCheckingPipelineOutput(BaseModel):
    """Output schema for the complete fact-checking pipeline."""
    request_id: Optional[str] = Field(None, description="Request identifier")
    pipeline_version: str = Field(default="fact-checking-pipeline-v1.0", description="Pipeline version")
    
    # Outputs from each stage
    preprocess_data: Optional[Dict[str, Any]] = Field(None, description="Preprocessing results")
    claim_extraction: Optional[Dict[str, Any]] = Field(None, description="Extracted claims")
    claim_verifications: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Verification results for each claim"
    )
    
    # Summary
    total_claims: int = Field(default=0, description="Total number of claims processed")
    verification_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of all verifications")
    processing_completed_at: Optional[str] = Field(None, description="ISO-8601 timestamp when processing completed")

