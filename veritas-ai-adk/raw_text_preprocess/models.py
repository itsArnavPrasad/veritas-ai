# models.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class PreprocessData(BaseModel):
    """Simplified preprocessed data - only essential fields for fact-checking."""
    # Core content fields
    doc_id: Optional[str] = Field(None, description="Unique document id")
    title: Optional[str] = Field(None, description="Article title")
    canonical_text: Optional[str] = Field(
        None, description="Cleaned article body text with unnecessary content removed"
    )
    
    # Basic metadata
    author: Optional[str] = Field(None, description="Article author if available")
    published_at: Optional[str] = Field(
        None, description="ISO-8601 datetime string if available"
    )
    language: Optional[str] = Field(None, description="ISO language code e.g. 'en'")
    
    # Source information
    source_domain: Optional[str] = Field(None, description="Source domain name")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL")
    
    # Simple entity list (just entity names, no positions)
    entities: Optional[List[str]] = Field(
        None, 
        description="Simple list of entity names (persons, organizations, locations) mentioned in the text"
    )
    
    # Processing metadata
    preprocess_version: Optional[str] = Field(
        default="preproc-v2.0", description="Agent version identifier"
    )
    extracted_by: Optional[str] = Field(
        default="preprocessing_agent", description="Agent name"
    )
