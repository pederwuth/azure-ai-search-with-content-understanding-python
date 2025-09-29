#!/usr/bin/env python3
"""
Standalone Book Summarization Service

A FastAPI service that provides book summarization capabilities for markdown content.
This service runs independently and can be used by any client that needs book summarization.

Features:
- Progressive chapter-by-chapter analysis
- Comprehensive book summaries with themes and objectives
- RESTful API endpoints
- Swagger/OpenAPI documentation
- Health checks and monitoring

Usage:
    python summarization_service.py

Endpoints:
    GET /health - Health check
    POST /summarize - Summarize markdown content
    POST /summarize-file - Upload and summarize markdown file
    GET /docs - Interactive API documentation
"""

from src.core.models import BookSummary
from src.summarization.book_summarizer import ProgressiveBookSummarizer
import uvicorn
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))


# Import summarization components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API


class SummarizeRequest(BaseModel):
    book_title: str = Field(..., description="Title of the book")
    markdown_content: str = Field(...,
                                  description="Markdown content to summarize")

    class Config:
        json_schema_extra = {
            "example": {
                "book_title": "Sample Book",
                "markdown_content": "# Chapter 1: Introduction\n\nThis is the first chapter..."
            }
        }


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str


# Create FastAPI app
app = FastAPI(
    title="Book Summarization Service",
    description="Standalone service for progressive book summarization from markdown content",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global summarizer instance
summarizer: Optional[ProgressiveBookSummarizer] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the summarizer on startup"""
    global summarizer
    try:
        logger.info("Initializing Book Summarization Service...")

        # Check for required environment variables
        import os
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.error("❌ Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"   - {var}")
            logger.error(
                "💡 Please set these environment variables before starting the service")
            raise Exception(
                f"Missing environment variables: {', '.join(missing_vars)}")

        summarizer = ProgressiveBookSummarizer()
        logger.info("✅ Book Summarization Service initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize summarizer: {e}")
        logger.error("\n🔧 Setup Instructions:")
        logger.error(
            "1. Set AZURE_OPENAI_ENDPOINT to your Azure OpenAI endpoint")
        logger.error(
            "2. Set AZURE_OPENAI_CHAT_DEPLOYMENT_NAME to your deployment name")
        logger.error("3. Ensure Azure CLI is authenticated: az login")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if summarizer else "unhealthy",
        timestamp=datetime.now().isoformat(),
        service="book-summarization-service",
        version="1.0.0"
    )


@app.post("/summarize")
async def summarize_content(request: SummarizeRequest):
    """
    Summarize markdown content progressively

    Args:
        request: Contains book title and markdown content

    Returns:
        BookSummary: Progressive summary with chapters, themes, and objectives
    """
    if not summarizer:
        raise HTTPException(
            status_code=503, detail="Summarizer not initialized")

    try:
        logger.info(f"Starting summarization for book: {request.book_title}")

        # Process the markdown content
        book_summary = await asyncio.to_thread(
            summarizer.process_document_progressively,
            request.markdown_content,
            request.book_title
        )

        logger.info(
            f"✅ Successfully summarized '{request.book_title}' with {len(book_summary.chapter_summaries)} chapters")

        # Convert to dict for JSON response
        import json
        return json.loads(json.dumps(book_summary, default=lambda o: o.__dict__))

    except Exception as e:
        logger.error(f"❌ Error summarizing content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Summarization failed: {str(e)}")


@app.post("/summarize-file")
async def summarize_file(
    file: UploadFile = File(..., description="Markdown file to summarize"),
    book_title: Optional[str] = Form(
        None, description="Optional book title (uses filename if not provided)")
):
    """
    Upload and summarize a markdown file

    Args:
        file: Uploaded markdown file
        book_title: Optional title (uses filename if not provided)

    Returns:
        BookSummary: Progressive summary with chapters, themes, and objectives
    """
    if not summarizer:
        raise HTTPException(
            status_code=503, detail="Summarizer not initialized")

    # Validate file type
    if not file.filename or not file.filename.endswith(('.md', '.markdown', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="File must be a markdown file (.md, .markdown, or .txt)"
        )

    try:
        # Read file content
        content = await file.read()
        markdown_content = content.decode('utf-8')

        # Use provided title or derive from filename
        title = book_title or (file.filename.replace('.md', '').replace(
            '.markdown', '').replace('.txt', '') if file.filename else "Unknown Book")

        logger.info(
            f"Starting file summarization for: {title} (file: {file.filename})")

        # Process the markdown content
        book_summary = await asyncio.to_thread(
            summarizer.process_document_progressively,
            markdown_content,
            title
        )

        logger.info(
            f"✅ Successfully summarized file '{file.filename}' with {len(book_summary.chapter_summaries)} chapters")

        # Convert to dict for JSON response
        import json
        return json.loads(json.dumps(book_summary, default=lambda o: o.__dict__))

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File must be valid UTF-8 text")
    except Exception as e:
        logger.error(f"❌ Error summarizing file: {e}")
        raise HTTPException(
            status_code=500, detail=f"File summarization failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


def main():
    """Run the summarization service"""
    print("🚀 Starting Book Summarization Service...")
    print("📚 Standalone service for progressive book summarization")
    print("🌐 Service will be available at: http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔍 Health Check: http://localhost:8001/health")
    print()

    # Run with uvicorn
    uvicorn.run(
        "summarization_service:app",
        host="0.0.0.0",
        port=8001,  # Different port from main service
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
