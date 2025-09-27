"""
FastAPI router for book summarization endpoints.

This router provides endpoints for:
1. Direct markdown summarization (for internal calls)
2. File upload and summarization (for standalone usage)
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

# Summarization components
try:
    from .book_summarizer import ProgressiveBookSummarizer
    from .models import BookSummary
    SUMMARIZATION_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import summarization components: {e}")
    SUMMARIZATION_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Get content output directory from environment or use default
CONTENT_OUTPUT_DIRECTORY = os.getenv(
    "CONTENT_OUTPUT_DIRECTORY", "content/books")

# Create router
router = APIRouter(
    prefix="/summarization",
    tags=["Book Summarization"]
)

# Request/Response Models


class SummarizationRequest(BaseModel):
    markdown_content: str
    title: str


class SummarizationResponse(BaseModel):
    summary: BookSummary
    processing_time_seconds: float
    timestamp: str


class SummarizationUploadResponse(BaseModel):
    summary: BookSummary
    processing_time_seconds: float
    timestamp: str
    saved_files: dict
    output_directory: str
    job_id: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str
    summarization_available: bool


# Initialize summarizer (will be lazy-loaded)
_summarizer = None


def get_summarizer():
    """Get or create the summarizer instance"""
    global _summarizer
    if _summarizer is None and SUMMARIZATION_AVAILABLE:
        _summarizer = ProgressiveBookSummarizer()
    return _summarizer


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for summarization service"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="book-summarization-router",
        version="1.0.0",
        summarization_available=SUMMARIZATION_AVAILABLE
    )


@router.post("/summarize", response_model=SummarizationResponse)
async def summarize_markdown(request: SummarizationRequest):
    """
    Summarize markdown content directly.

    This endpoint is used internally by the document processor
    and can also be called directly with markdown content.
    """
    if not SUMMARIZATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Summarization service is not available. Please check Azure OpenAI configuration."
        )

    summarizer = get_summarizer()
    if not summarizer:
        raise HTTPException(
            status_code=503,
            detail="Failed to initialize summarization service"
        )

    start_time = datetime.now()
    logger.info(f"Starting markdown summarization for: {request.title}")

    try:
        # Process the markdown content
        book_summary = await asyncio.to_thread(
            summarizer.process_document_progressively,
            request.markdown_content,
            request.title
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Completed summarization for '{request.title}' in {processing_time:.2f} seconds")

        return SummarizationResponse(
            summary=book_summary,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/upload", response_model=SummarizationUploadResponse)
async def upload_and_summarize(
    file: UploadFile = File(...),
    book_title: Optional[str] = Form(None)
):
    """
    Upload a markdown file and get a summary.

    This endpoint allows standalone usage where users can upload
    markdown files directly for summarization. Results are saved
    to the content output directory.
    """
    if not SUMMARIZATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Summarization service is not available. Please check Azure OpenAI configuration."
        )

    summarizer = get_summarizer()
    if not summarizer:
        raise HTTPException(
            status_code=503,
            detail="Failed to initialize summarization service"
        )

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

        # Handle empty string or placeholder values as None for book_title (same as enhanced API)
        if book_title in ("", "string", None):
            book_title = None

        # Use provided title or derive from filename
        title = book_title or (file.filename.replace('.md', '').replace(
            '.markdown', '').replace('.txt', '') if file.filename else "Unknown Book")

        logger.info(
            f"Starting file summarization for: {title} (file: {file.filename})")
        start_time = datetime.now()

        # Create directory structure similar to enhanced document processor
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = str(uuid.uuid4()).split('-')[0]

        # Create folder structure: {book_title}-book-{timestamp}-{job_id}
        safe_title = "".join(c for c in title if c.isalnum()
                             or c in (' ', '-', '_')).rstrip()
        # Limit length and replace spaces
        safe_title = safe_title.replace(' ', '_')[:50]

        main_folder_name = f"{safe_title}-book-{timestamp}-{job_id}"
        main_output_path = Path(CONTENT_OUTPUT_DIRECTORY) / main_folder_name

        # Create folder structure
        input_dir = main_output_path / "input"
        processed_dir = main_output_path / "processed"
        summaries_dir = processed_dir / \
            f"{safe_title}-book-summaries-{timestamp}-{job_id}"

        # Create all directories with proper error handling
        try:
            main_output_path.mkdir(parents=True, exist_ok=True)
            input_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            summaries_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory structure: {summaries_dir}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create output directories: {e}")

        # Save the original markdown file to input directory
        input_file_path = input_dir / file.filename
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Process the markdown content
        book_summary = await asyncio.to_thread(
            summarizer.process_document_progressively,
            markdown_content,
            title
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Save summary as JSON with error handling
        summary_json_path = summaries_dir / \
            f"{safe_title}-summary-{timestamp}-{job_id}.json"
        try:
            logger.info(f"Saving JSON summary to: {summary_json_path}")
            with open(summary_json_path, 'w', encoding='utf-8') as f:
                # Convert BookSummary to dict for JSON serialization
                summary_dict = {
                    "book_title": book_summary.book_title,
                    "overall_summary": book_summary.overall_summary,
                    "key_themes": book_summary.key_themes,
                    "learning_objectives": book_summary.learning_objectives,
                    "total_chapters": book_summary.total_chapters,
                    "created_at": book_summary.created_at.isoformat() if book_summary.created_at else None,
                    "chapter_summaries": [
                        {
                            "chapter_number": ch.chapter_number,
                            "chapter_title": ch.chapter_title,
                            "summary": ch.summary,
                            "key_concepts": ch.key_concepts,
                            "main_topics": ch.main_topics,
                            "token_count": ch.token_count,
                            "created_at": ch.created_at.isoformat() if ch.created_at else None
                        } for ch in book_summary.chapter_summaries
                    ]
                }
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved JSON summary")
        except Exception as e:
            logger.error(f"Failed to save JSON summary: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to save summary files: {e}")

        # Save summary as formatted markdown
        summary_md_path = summaries_dir / \
            f"{safe_title}-summary-{timestamp}-{job_id}.md"
        try:
            logger.info(f"Saving markdown summary to: {summary_md_path}")
            with open(summary_md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {book_summary.book_title}\n\n")
                f.write(
                    f"## Overall Summary\n{book_summary.overall_summary}\n\n")
                f.write(f"## Key Themes\n")
                for theme in book_summary.key_themes:
                    f.write(f"- {theme}\n")
                f.write(f"\n## Learning Objectives\n")
                for objective in book_summary.learning_objectives:
                    f.write(f"- {objective}\n")
                f.write(f"\n## Chapter Summaries\n")
                for ch in book_summary.chapter_summaries:
                    f.write(
                        f"\n### Chapter {ch.chapter_number}: {ch.chapter_title}\n")
                    f.write(f"{ch.summary}\n\n")
                    f.write(f"**Key Concepts:**\n")
                    for concept in ch.key_concepts:
                        f.write(f"- {concept}\n")
                    f.write(f"\n**Main Topics:**\n")
                    for topic in ch.main_topics:
                        f.write(f"- {topic}\n")
                    f.write("\n")
                f.write(f"\n## Summary Statistics\n")
                f.write(
                    f"- **Total Chapters:** {book_summary.total_chapters}\n")
                f.write(
                    f"- **Created At:** {book_summary.created_at.isoformat() if book_summary.created_at else 'Unknown'}\n")
            logger.info(f"Successfully saved markdown summary")
        except Exception as e:
            logger.error(f"Failed to save markdown summary: {e}")
            # Don't raise here, continue with metadata

        # Create metadata file
        metadata_path = main_output_path / "metadata.json"
        metadata = {
            "job_id": job_id,
            "book_title": title,
            "content_type": "book",
            "created_at": datetime.now().isoformat() + "Z",
            "status": "completed",
            "input_file": file.filename,
            "processing_pipeline": "summarization_service",
            "processing_time_seconds": processing_time,
            "folder_structure": "v1",
            "naming_convention": "{book_title}-{content_type}-{subtype}-{timestamp}-{job_id}",
            "output_files": {
                "input_markdown": f"input/{file.filename}",
                "summary_json": f"processed/{summaries_dir.name}/{summary_json_path.name}",
                "summary_markdown": f"processed/{summaries_dir.name}/{summary_md_path.name}",
                "metadata": "metadata.json"
            }
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Completed file summarization for '{title}' in {processing_time:.2f} seconds")
        logger.info(f"Files saved to: {main_output_path}")

        return SummarizationUploadResponse(
            summary=book_summary,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat(),
            saved_files={
                "input_markdown": str(input_file_path),
                "summary_json": str(summary_json_path),
                "summary_markdown": str(summary_md_path),
                "metadata": str(metadata_path)
            },
            output_directory=str(main_output_path),
            job_id=job_id
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(f"Error during file summarization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File summarization failed: {str(e)}"
        )
