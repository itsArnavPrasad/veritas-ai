"""
File upload endpoints for saving images and videos
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from services.storage import save_uploaded_file

router = APIRouter()


@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload and save an image file
    
    Accepts: image/jpeg, image/png, image/gif, image/webp
    
    Returns:
        {
            "file_id": "uuid",
            "file_path": "path/to/file",
            "filename": "stored_filename.jpg",
            "original_filename": "original.jpg",
            "file_type": "image",
            "content_type": "image/jpeg",
            "size": 12345,
            "saved_at": "2024-01-01T00:00:00"
        }
    """
    try:
        # Validate content type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected image, got: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size (e.g., max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size / (1024*1024)}MB"
            )
        
        # Save file
        file_info = await save_uploaded_file(
            file_content=content,
            filename=file.filename or "image",
            file_type="image",
            content_type=file.content_type
        )
        
        return JSONResponse(
            status_code=200,
            content=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )


@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload and save a video file
    
    Accepts: video/mp4, video/quicktime, video/x-msvideo, video/webm
    
    Returns:
        {
            "file_id": "uuid",
            "file_path": "path/to/file",
            "filename": "stored_filename.mp4",
            "original_filename": "original.mp4",
            "file_type": "video",
            "content_type": "video/mp4",
            "size": 12345678,
            "saved_at": "2024-01-01T00:00:00"
        }
    """
    try:
        # Validate content type
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected video, got: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size (e.g., max 500MB for videos)
        max_size = 500 * 1024 * 1024  # 500MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size / (1024*1024)}MB"
            )
        
        # Save file
        file_info = await save_uploaded_file(
            file_content=content,
            filename=file.filename or "video",
            file_type="video",
            content_type=file.content_type
        )
        
        return JSONResponse(
            status_code=200,
            content=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading video: {str(e)}"
        )

