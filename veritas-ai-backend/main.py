"""
Veritas AI Backend - Main FastAPI Application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Load environment variables from .env file
# Get the backend directory (where this file is located)
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

from config import API_PREFIX
from services.database import init_db
from routers import verify, results, stream, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield
    # Cleanup if needed


app = FastAPI(
    title="Veritas AI API",
    description="Misinformation Verification Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(verify.router, prefix=API_PREFIX, tags=["verification"])
app.include_router(results.router, prefix=API_PREFIX, tags=["results"])
app.include_router(stream.router, prefix=API_PREFIX, tags=["streaming"])
app.include_router(upload.router, prefix=API_PREFIX, tags=["upload"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Veritas AI Backend",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

