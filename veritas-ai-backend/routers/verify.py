"""
Verification endpoints
"""
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from services.database import get_db
from models.verification import Verification, InputType, VerificationStatus
from services.storage import create_verification_storage, save_input_file, save_text_input
from services.pipeline import run_pipeline

router = APIRouter()


class TextVerificationRequest(BaseModel):
    """Text verification request"""
    text: str


class ArticleVerificationRequest(BaseModel):
    """Article verification request"""
    url: Optional[HttpUrl] = None
    html_content: Optional[str] = None


class TweetVerificationRequest(BaseModel):
    """Tweet verification request"""
    tweet_text: str
    tweet_url: Optional[str] = None
    media_urls: Optional[list[str]] = []


@router.post("/verify/text")
async def verify_text(
    request: TextVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify plain text input
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.TEXT,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save input text
        await save_text_input(verification.id, request.text)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.TEXT)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating verification: {str(e)}")


@router.post("/verify/image")
async def verify_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify image file upload
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.IMAGE,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Read file content
        content = await file.read()
        
        # Save uploaded file
        filename = file.filename or f"image_{verification.id}.{file.content_type.split('/')[-1] if file.content_type else 'jpg'}"
        await save_input_file(verification.id, filename, content)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.IMAGE)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/verify/video")
async def verify_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify video file upload
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.VIDEO,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Read file content
        content = await file.read()
        
        # Save uploaded file
        filename = file.filename or f"video_{verification.id}.{file.content_type.split('/')[-1] if file.content_type else 'mp4'}"
        await save_input_file(verification.id, filename, content)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.VIDEO)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@router.post("/verify/article")
async def verify_article(
    request: ArticleVerificationRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify article (URL or HTML content)
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.ARTICLE,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save input
        if request.url:
            # Save URL
            url_content = f"URL: {request.url}\n"
            await save_text_input(verification.id, url_content)
        elif request.html_content:
            # Save HTML content
            await save_text_input(verification.id, request.html_content)
        else:
            raise HTTPException(status_code=400, detail="Either url or html_content must be provided")
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.ARTICLE)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing article: {str(e)}")


@router.post("/verify/tweet")
async def verify_tweet(
    request: TweetVerificationRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify a tweet (text and optional media)
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.TEXT,  # Treat tweets as text for now
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save tweet text
        tweet_content = f"Tweet Text: {request.tweet_text}\n"
        if request.tweet_url:
            tweet_content += f"Tweet URL: {request.tweet_url}\n"
        if request.media_urls:
            tweet_content += f"Media URLs: {', '.join(request.media_urls)}\n"
        
        await save_text_input(verification.id, tweet_content)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.TEXT)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing tweet: {str(e)}")

