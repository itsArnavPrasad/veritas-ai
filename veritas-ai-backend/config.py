"""
Configuration settings for Veritas AI Backend
"""
import os
from pathlib import Path

# Database Configuration
# Default connection uses system username (no password for local connections on macOS)
# You can override this with POSTGRES_URL environment variable
POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://arnavprasad@localhost:5432/veritas_ai"
)

# Storage Configuration
BASE_DIR = Path(__file__).parent
STORAGE_ROOT = BASE_DIR / "storage" / "verifications"

# Ensure storage directory exists
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

# API Configuration
API_PREFIX = "/api/v1"

# Pipeline Configuration
PIPELINE_STAGES = [
    "preprocessing",
    "claim_extraction",
    "retrieval",
    "forensics",
    "consistency",
    "final_verdict"
]

