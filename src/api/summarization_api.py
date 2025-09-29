"""
FastAPI endpoints for book summarization.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from ..summarization.book_summarizer import ProgressiveBookSummarizer
from ..summarization.models import BookSummary

logger = logging.getLogger(__name__)

# Create router for book summarization endpoints
router = APIRouter(prefix="/summarization", tags=["Book Summarization"])


class SummarizationRequest(BaseModel):
    """Request model for book summarization."""
    book_title: Optional[str] = Field(
        default=None, description="Title of the book")
    markdown_content: str = Field(
        description="Full markdown content of the book")


class SummarizationResponse(BaseModel):
    """Response model for book summarization."""
    success: bool
    book_title: str
    total_chapters: int
    processing_time_seconds: float
    total_tokens_used: int
    summary_id: str
    final_summary: str
    error: Optional[str] = None


# Global summarizer instance (will be initialized on first use)
_summarizer_instance: Optional[ProgressiveBookSummarizer] = None


def get_summarizer() -> ProgressiveBookSummarizer:
    """Get or create summarizer instance."""
    global _summarizer_instance

    if _summarizer_instance is None:
        # Initialize Azure OpenAI client
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default")

        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=token_provider,
            azure_deployment=os.getenv(
                "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-5-mini"),
            api_version=os.getenv(
                "AZURE_OPENAI_CHAT_API_VERSION", "2024-08-01-preview")
        )

        _summarizer_instance = ProgressiveBookSummarizer(llm)
        logger.info("Book summarizer initialized")

    return _summarizer_instance


@router.post("/summarize", response_model=SummarizationResponse)
async def summarize_book(request: SummarizationRequest) -> SummarizationResponse:
    """
    Summarize a book using progressive chapter-by-chapter analysis.

    This endpoint processes markdown content of a book and creates:
    - Individual chapter summaries
    - Progressive context building
    - Final comprehensive book summary
    """
    try:
        logger.info(
            f"Starting book summarization for: {request.book_title or 'Unknown Book'}")

        # Get summarizer instance
        summarizer = get_summarizer()

        # Process the book
        book_summary = summarizer.process_document_progressively(
            markdown_content=request.markdown_content,
            book_title=request.book_title or "Unknown Book"
        )

        # Generate unique summary ID
        summary_id = f"summary_{book_summary.created_at.strftime('%Y%m%d_%H%M%S')}"

        return SummarizationResponse(
            success=True,
            book_title=book_summary.book_title,
            total_chapters=book_summary.total_chapters,
            processing_time_seconds=0.0,  # We don't track this in the API yet
            total_tokens_used=0,  # We don't track this in the API yet
            summary_id=summary_id,
            final_summary=book_summary.overall_summary
        )

    except Exception as e:
        logger.error(f"Book summarization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/summarize-file", response_model=SummarizationResponse)
async def summarize_book_file(
    file: UploadFile = File(...,
                            description="Markdown file containing book content"),
    book_title: Optional[str] = Form(None, description="Optional book title")
) -> SummarizationResponse:
    """
    Summarize a book from uploaded markdown file.

    Upload a .md file containing the full book content for summarization.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith('.md'):
            raise HTTPException(
                status_code=400,
                detail="Only .md (markdown) files are supported"
            )

        # Read file content
        content = await file.read()
        markdown_content = content.decode('utf-8')

        # Use filename as title if not provided
        if not book_title and file.filename:
            book_title = Path(file.filename).stem

        # Create request and process
        request = SummarizationRequest(
            book_title=book_title,
            markdown_content=markdown_content
        )

        return await summarize_book(request)

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(f"File summarization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File summarization failed: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for summarization service."""
    try:
        # Try to get summarizer (initializes if needed)
        get_summarizer()
        return {"status": "healthy", "service": "book_summarization"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
