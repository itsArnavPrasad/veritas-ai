"""
Local file storage utilities
"""
import json
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID

from config import STORAGE_ROOT


def get_verification_storage_path(verification_id: UUID) -> Path:
    """Get the storage path for a verification"""
    return STORAGE_ROOT / str(verification_id)


def create_verification_storage(verification_id: UUID) -> Path:
    """Create storage directories for a verification"""
    base_path = get_verification_storage_path(verification_id)
    input_path = base_path / "input"
    output_path = base_path / "outputs"
    
    input_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)
    
    return base_path


async def save_input_file(verification_id: UUID, filename: str, content: bytes) -> Path:
    """Save an input file to storage"""
    storage_path = get_verification_storage_path(verification_id)
    input_path = storage_path / "input" / filename
    
    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)
    
    return input_path


async def save_text_input(verification_id: UUID, text: str) -> Path:
    """Save text input to a file"""
    storage_path = get_verification_storage_path(verification_id)
    input_path = storage_path / "input" / "input.txt"
    
    async with aiofiles.open(input_path, "w", encoding="utf-8") as f:
        await f.write(text)
    
    return input_path


async def save_claims_json(verification_id: UUID, claims: list) -> Path:
    """Save claims to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "claims.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(claims, indent=2, ensure_ascii=False))
    
    return output_path


async def save_results_json(verification_id: UUID, results: Dict[str, Any]) -> Path:
    """Save results to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "results.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(results, indent=2, ensure_ascii=False))
    
    return output_path


async def append_log(verification_id: UUID, log_entry: Dict[str, Any]) -> None:
    """Append a log entry to logs.json"""
    storage_path = get_verification_storage_path(verification_id)
    logs_path = storage_path / "outputs" / "logs.json"
    
    # Read existing logs if file exists
    logs = []
    if logs_path.exists():
        async with aiofiles.open(logs_path, "r", encoding="utf-8") as f:
            content = await f.read()
            if content:
                logs = json.loads(content)
    
    # Append new log entry
    logs.append(log_entry)
    
    # Write back
    async with aiofiles.open(logs_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(logs, indent=2, ensure_ascii=False))


async def read_results_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read results from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    results_path = storage_path / "outputs" / "results.json"
    
    if not results_path.exists():
        return None
    
    async with aiofiles.open(results_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def read_claims_json(verification_id: UUID) -> Optional[list]:
    """Read claims from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    claims_path = storage_path / "outputs" / "claims.json"
    
    if not claims_path.exists():
        return None
    
    async with aiofiles.open(claims_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)

