"""
Local file storage utilities
"""
import json
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

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


async def save_results_json(verification_id: UUID, results: Dict[str, Any]) -> Path:
    """Save results to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "results.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(results, indent=2, ensure_ascii=False))
    
    return output_path


async def read_results_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read results from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    results_path = storage_path / "outputs" / "results.json"
    
    if not results_path.exists():
        return None
    
    async with aiofiles.open(results_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def save_text_analysis_json(verification_id: UUID, text_analysis: Dict[str, Any]) -> Path:
    """Save text analysis to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "text_analysis.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(text_analysis, indent=2, ensure_ascii=False))
    
    return output_path


async def save_image_analysis_json(verification_id: UUID, image_analysis: Dict[str, Any]) -> Path:
    """Save image analysis to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "image_analysis.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(image_analysis, indent=2, ensure_ascii=False))
    
    return output_path


async def save_video_analysis_json(verification_id: UUID, video_analysis: Dict[str, Any]) -> Path:
    """Save video analysis to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "video_analysis.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(video_analysis, indent=2, ensure_ascii=False))
    
    return output_path


async def save_fusion_results_json(verification_id: UUID, fusion_results: Dict[str, Any]) -> Path:
    """Save fusion results to JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    output_path = storage_path / "outputs" / "fusion_results.json"
    
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(fusion_results, indent=2, ensure_ascii=False))
    
    return output_path


async def read_text_analysis_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read text analysis from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    text_path = storage_path / "outputs" / "text_analysis.json"
    
    if not text_path.exists():
        return None
    
    async with aiofiles.open(text_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def read_image_analysis_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read image analysis from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    image_path = storage_path / "outputs" / "image_analysis.json"
    
    if not image_path.exists():
        return None
    
    async with aiofiles.open(image_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def read_video_analysis_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read video analysis from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    video_path = storage_path / "outputs" / "video_analysis.json"
    
    if not video_path.exists():
        return None
    
    async with aiofiles.open(video_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def read_fusion_results_json(verification_id: UUID) -> Optional[Dict[str, Any]]:
    """Read fusion results from JSON file"""
    storage_path = get_verification_storage_path(verification_id)
    fusion_path = storage_path / "outputs" / "fusion_results.json"
    
    if not fusion_path.exists():
        return None
    
    async with aiofiles.open(fusion_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


# File Upload Storage Functions

def get_uploads_storage_path() -> Path:
    """Get the storage path for uploaded files"""
    uploads_path = STORAGE_ROOT.parent / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    return uploads_path


def get_upload_type_path(file_type: str) -> Path:
    """Get storage path for a specific file type (image/video)"""
    uploads_path = get_uploads_storage_path()
    type_path = uploads_path / file_type
    type_path.mkdir(parents=True, exist_ok=True)
    return type_path


async def save_uploaded_file(
    file_content: bytes,
    filename: str,
    file_type: str,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save an uploaded file (image or video) to storage
    
    Args:
        file_content: The file content as bytes
        filename: Original filename
        file_type: 'image' or 'video'
        content_type: MIME type of the file
        
    Returns:
        Dictionary with file_id, file_path, filename, file_type, size, and saved_at
    """
    # Generate unique file ID
    file_id = str(uuid4())
    
    # Get storage path for file type
    type_path = get_upload_type_path(file_type)
    
    # Preserve original extension or infer from content type
    original_ext = Path(filename).suffix if filename else ""
    if not original_ext and content_type:
        # Infer extension from content type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/x-msvideo": ".avi",
            "video/webm": ".webm",
        }
        original_ext = ext_map.get(content_type, "")
    
    # Create filename with UUID to avoid collisions
    stored_filename = f"{file_id}{original_ext}"
    file_path = type_path / stored_filename
    
    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    
    # Return file metadata
    return {
        "file_id": file_id,
        "file_path": str(file_path),
        "filename": stored_filename,
        "original_filename": filename,
        "file_type": file_type,
        "content_type": content_type,
        "size": len(file_content),
        "saved_at": datetime.utcnow().isoformat()
    }


async def get_uploaded_file(file_id: str, file_type: str) -> Optional[Path]:
    """
    Get the path to an uploaded file by ID and type
    
    Args:
        file_id: The file ID (UUID string)
        file_type: 'image' or 'video'
        
    Returns:
        Path to the file if found, None otherwise
    """
    type_path = get_upload_type_path(file_type)
    
    # Search for file with this ID (check all extensions)
    possible_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".webm"]
    for ext in possible_extensions:
        file_path = type_path / f"{file_id}{ext}"
        if file_path.exists():
            return file_path
    
    return None


async def delete_uploaded_file(file_id: str, file_type: str) -> bool:
    """
    Delete an uploaded file by ID and type
    
    Args:
        file_id: The file ID (UUID string)
        file_type: 'image' or 'video'
        
    Returns:
        True if file was deleted, False otherwise
    """
    file_path = await get_uploaded_file(file_id, file_type)
    if file_path and file_path.exists():
        file_path.unlink()
        return True
    return False

