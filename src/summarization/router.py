"""
FastAPI router for educational content summarization.

Provides endpoints for uploading markdown files and generating progressive summaries.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from .book_summarizer import ProgressiveBookSummarizer
from .models import SummarizationResult

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summarization", tags=["Educational Summarization"])


def create_summary_output_path(original_filename: str, content_type: str = "book") -> Path:
    """Create output path following the naming convention, preserving original timestamps and IDs"""
    # Remove file extension
    base_name = Path(original_filename).stem
    
    # Check if the filename follows the expected convention: name-type-timestamp-id
    # Example: venture_deals_(21)-book-markdown-20250928_223659-0095c30d
    parts = base_name.split('-')
    
    if len(parts) >= 4 and len(parts[-1]) == 8 and len(parts[-2]) == 15:
        # File follows the convention, extract components
        unique_id = parts[-1]  # e.g., "0095c30d"
        timestamp = parts[-2]  # e.g., "20250928_223659"
        file_type = parts[-3]  # e.g., "markdown"
        existing_content_type = parts[-4]  # e.g., "book"
        
        # Reconstruct the name part (everything before the last 4 components)
        name_parts = parts[:-4]
        name_base = '-'.join(name_parts)  # e.g., "venture_deals_(21)"
        
        # Create the folder structure using existing content type
        # Book folder: {name}-{existing_content_type}-{timestamp}-{id}
        book_folder = f"{name_base}-{existing_content_type}-{timestamp}-{unique_id}"
        
        # Summary folder: {name}-{existing_content_type}-summary-{timestamp}-{id}
        summary_folder = f"{name_base}-{existing_content_type}-summary-{timestamp}-{unique_id}"
    else:
        # File doesn't follow convention, create new timestamp and ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        book_folder = f"{base_name}-{content_type}-{timestamp}-{unique_id}"
        summary_folder = f"{base_name}-{content_type}-summary-{timestamp}-{unique_id}"
    
    output_path = Path("content/books") / book_folder / "processed" / summary_folder
    return output_path


@router.post("/generate-from-markdown")
async def generate_summary_from_markdown(
    file: UploadFile = File(..., description="Markdown file to summarize"),
    custom_filename: Optional[str] = Form(None, description="Custom filename for output"),
    content_type: str = Form("book", description="Type of content (book, article, etc.)")
):
    """
    Generate educational summaries from an uploaded markdown file.
    
    Creates progressive chapter-by-chapter summaries and a comprehensive book overview.
    Results are saved following the naming convention in the processed folder structure.
    
    Args:
        file: Markdown file (.md) containing the content to summarize
        custom_filename: Optional custom filename for output files
        content_type: Type of content being processed (default: "book")
        
    Returns:
        JSON response with summary details and file locations
    """
    
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith('.md'):
            raise HTTPException(
                status_code=400, 
                detail="Only markdown files (.md) are supported"
            )
        
        logger.info(f"📚 Starting summarization for: {file.filename}")
        logger.info(f"📋 Form parameters - custom_filename: '{custom_filename}', content_type: '{content_type}'")
        
        # Read the markdown content
        markdown_content = await file.read()
        markdown_text = markdown_content.decode('utf-8')
        
        logger.info(f"📄 Read {len(markdown_text):,} characters from {file.filename}")
        
        # Determine output filename - handle Swagger UI defaults
        if custom_filename and custom_filename.strip() and custom_filename.lower() != "string":
            original_filename = custom_filename.strip()
        elif file.filename:
            # Use the actual uploaded filename (without extension)
            original_filename = Path(file.filename).stem
        else:
            # Fallback if no filename available
            original_filename = "document"
        
        logger.info(f"📝 Using filename: {original_filename} (from {'custom input' if custom_filename and custom_filename.strip() and custom_filename.lower() != 'string' else 'uploaded file'})")
        
        # Create output directory path
        output_directory = create_summary_output_path(original_filename, content_type)
        logger.info(f"📁 Output directory: {output_directory}")
        
        # Initialize summarizer
        summarizer = ProgressiveBookSummarizer()
        
        # Process the document
        start_time = time.time()
        
        result = summarizer.process_document_progressively(
            markdown_content=markdown_text,
            output_directory=output_directory,
            original_filename=original_filename
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Summarization completed in {processing_time:.2f} seconds")
        
        # Return response
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Educational summary generated successfully",
                "book_title": result.book_summary.book_title,
                "total_chapters": result.book_summary.total_chapters,
                "key_themes_count": len(result.book_summary.key_themes),
                "learning_objectives_count": len(result.book_summary.learning_objectives),
                "output_directory": str(result.output_directory),
                "summary_file": str(result.summary_file),
                "metadata_file": str(result.metadata_file),
                "processing_time_seconds": result.processing_time_seconds,
                "created_at": result.book_summary.created_at.isoformat(),
                "files_created": {
                    "book_summary": str(result.summary_file.name),
                    "metadata": str(result.metadata_file.name)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Summarization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@router.get("/status")
async def get_summarization_status():
    """
    Get the status of the summarization service.
    
    Returns:
        Service status and available endpoints
    """
    return {
        "status": "active",
        "service": "Educational Content Summarization",
        "version": "1.0.0",
        "capabilities": [
            "Progressive chapter summarization",
            "Comprehensive book overviews", 
            "Key concept extraction",
            "Learning objectives generation",
            "Educational theme identification"
        ],
        "supported_formats": ["markdown (.md)"],
        "endpoints": {
            "generate_summary": "/summarization/generate-from-markdown",
            "status": "/summarization/status"
        }
    }


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "summarization",
        "timestamp": datetime.now().isoformat()
    }