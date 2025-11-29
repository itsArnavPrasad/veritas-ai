"""
Results endpoints
"""
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID

from services.database import get_db
from models.verification import Verification
from services.storage import (
    read_results_json,
    read_text_analysis_json,
    read_image_analysis_json,
    read_video_analysis_json,
    read_fusion_results_json,
    get_verification_storage_path,
    get_upload_type_path
)
from config import STORAGE_ROOT

router = APIRouter()


@router.get("/result/{verification_id}")
async def get_result(
    verification_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get verification results
    """
    # Get verification from database
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Read all analysis files (only those that exist)
    text_analysis = await read_text_analysis_json(verification_id)
    image_analysis = await read_image_analysis_json(verification_id)
    video_analysis = await read_video_analysis_json(verification_id)
    fusion_results = await read_fusion_results_json(verification_id)
    
    # Check if any results exist
    has_results = text_analysis or image_analysis or video_analysis or fusion_results
    
    if not has_results:
        # Try to read legacy results.json for backward compatibility
        legacy_results = await read_results_json(verification_id)
        if legacy_results:
            return {
                "verification_id": str(verification_id),
                "status": legacy_results.get("status", verification.status.value),
                "timestamp": legacy_results.get("timestamp"),
                "fusion_results": legacy_results.get("fusion_results", {}),
                "all_outputs": legacy_results.get("all_outputs", {})
            }
        
        # Return basic status if results not ready
        return {
            "verification_id": str(verification_id),
            "status": verification.status.value,
            "message": "Results not yet available"
        }
    
    # Get timestamp from fusion results or use current time
    timestamp = fusion_results.get("fusion_timestamp") if fusion_results else datetime.utcnow().isoformat()
    
    # Find input files (image/video) - files should be named with verification_id
    input_files = []
    verification_id_str = str(verification_id)
    
    # Check verification input directory first
    input_path = get_verification_storage_path(verification_id) / "input"
    print(f"Looking for input files in: {input_path}")
    if input_path.exists():
        print(f"Input path exists, listing files...")
        for file_path in input_path.iterdir():
            if file_path.is_file():
                print(f"Found file: {file_path.name}")
                # Check if it's an image or video
                ext = file_path.suffix.lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    input_files.append({
                        "type": "image",
                        "filename": file_path.name,
                        "path": f"/api/v1/result/{verification_id}/input/{file_path.name}"
                    })
                elif ext in ['.mp4', '.mov', '.avi', '.webm']:
                    input_files.append({
                        "type": "video",
                        "filename": file_path.name,
                        "path": f"/api/v1/result/{verification_id}/input/{file_path.name}"
                    })
    else:
        print(f"Input path does not exist: {input_path}")
    
    # Also check uploads directory for files named with verification_id
    if len(input_files) == 0:
        print("No files in verification input, checking uploads directory for verification_id-based files...")
        # Check image uploads - look for file named {verification_id}.ext
        image_uploads_path = get_upload_type_path("image")
        if image_uploads_path.exists():
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                potential_file = image_uploads_path / f"{verification_id_str}{ext}"
                if potential_file.exists() and potential_file.is_file():
                    input_files.append({
                        "type": "image",
                        "filename": potential_file.name,
                        "path": f"/api/v1/result/{verification_id}/input/{potential_file.name}"
                    })
                    print(f"Found image in uploads: {potential_file.name}")
        
        # Check video uploads - look for file named {verification_id}.ext
        video_uploads_path = get_upload_type_path("video")
        if video_uploads_path.exists():
            for ext in ['.mp4', '.mov', '.avi', '.webm']:
                potential_file = video_uploads_path / f"{verification_id_str}{ext}"
                if potential_file.exists() and potential_file.is_file():
                    input_files.append({
                        "type": "video",
                        "filename": potential_file.name,
                        "path": f"/api/v1/result/{verification_id}/input/{potential_file.name}"
                    })
                    print(f"Found video in uploads: {potential_file.name}")
    
    print(f"Found {len(input_files)} input files: {input_files}")
    
    # Return results from separate files
    return {
        "verification_id": str(verification_id),
        "status": verification.status.value if verification.status.value == "done" else "done",
        "timestamp": timestamp,
        # Individual analysis results
        "text_analysis": text_analysis,
        "image_analysis": image_analysis,
        "video_analysis": video_analysis,
        "fusion_results": fusion_results,
        # Input files for display
        "input_files": input_files
    }


@router.get("/result/{verification_id}/input/{filename}")
async def get_input_file(
    verification_id: UUID,
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Serve input files (images/videos) for a verification
    """
    print(f"Serving file request: verification_id={verification_id}, filename={filename}")
    
    # Verify the verification exists
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        print(f"Verification not found: {verification_id}")
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Determine file type from extension first
    ext = Path(filename).suffix.lower()
    file_type = None
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        file_type = "image"
    elif ext in ['.mp4', '.mov', '.avi', '.webm']:
        file_type = "video"
    
    file_path = None
    
    # First, try to get the file from verification input directory
    input_path = get_verification_storage_path(verification_id) / "input" / filename
    print(f"Looking for file at: {input_path}")
    
    if input_path.exists() and input_path.is_file():
        file_path = input_path
        print(f"File found in verification input: {input_path}")
    
    # Fallback: check uploads directory (files should be named with verification_id)
    if not file_path and file_type:
        print(f"File not in verification input, checking uploads directory...")
        # Try the exact filename first
        uploads_path = get_upload_type_path(file_type) / filename
        print(f"Checking uploads path: {uploads_path}")
        if uploads_path.exists() and uploads_path.is_file():
            file_path = uploads_path
            print(f"File found in uploads: {uploads_path}")
        else:
            # Also try with verification_id as filename (in case file was renamed)
            verification_id_str = str(verification_id)
            verification_based_file = get_upload_type_path(file_type) / f"{verification_id_str}{ext}"
            if verification_based_file.exists() and verification_based_file.is_file():
                file_path = verification_based_file
                print(f"File found in uploads with verification_id name: {verification_based_file}")
            else:
                print(f"File not found in uploads: {uploads_path} or {verification_based_file}")
    
    if not file_path or not file_path.exists():
        print(f"File not found anywhere: {filename}")
        print(f"Checked paths:")
        print(f"  - Verification input: {input_path}")
        if file_type:
            print(f"  - Uploads ({file_type}): {get_upload_type_path(file_type) / filename}")
            print(f"  - Uploads with verification_id: {get_upload_type_path(file_type) / f'{verification_id}{ext}'}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    print(f"File found, serving: {file_path}")
    
    # Determine media type from file extension
    ext = file_path.suffix.lower()
    media_type = None
    if ext in ['.jpg', '.jpeg']:
        media_type = 'image/jpeg'
    elif ext == '.png':
        media_type = 'image/png'
    elif ext == '.gif':
        media_type = 'image/gif'
    elif ext == '.webp':
        media_type = 'image/webp'
    elif ext == '.mp4':
        media_type = 'video/mp4'
    elif ext == '.mov':
        media_type = 'video/quicktime'
    elif ext == '.avi':
        media_type = 'video/x-msvideo'
    elif ext == '.webm':
        media_type = 'video/webm'
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

