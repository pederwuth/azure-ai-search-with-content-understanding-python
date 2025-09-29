"""
FastAPI server for Educational Content Understanding Pipeline.

This API provides endpoints to test and use the Content Understanding
implementation created in Phase 2.
"""

import os
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Environment configuration
CONTENT_OUTPUT_DIRECTORY = os.getenv(
    "CONTENT_OUTPUT_DIRECTORY", "content/books")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enhanced processing components (preferred)
try:
    from .enhanced_api import router as enhanced_router
    ENHANCED_PROCESSING_AVAILABLE = True
    logger.info("Enhanced processing components imported successfully")
except ImportError as e:
    logger.error(f"Failed to import enhanced processing components: {e}")
    ENHANCED_PROCESSING_AVAILABLE = False

# Summarization components
try:
    from .summarization.router import router as summarization_router
    SUMMARIZATION_AVAILABLE = True
    logger.info("Summarization components imported successfully")
except ImportError as e:
    logger.error(f"Failed to import summarization components: {e}")
    SUMMARIZATION_AVAILABLE = False

# FastAPI app configuration
app = FastAPI(
    title="Educational Content Understanding API",
    description="API for processing educational documents with Azure Content Understanding",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enhanced processing router if available
if ENHANCED_PROCESSING_AVAILABLE:
    app.include_router(enhanced_router)
    logger.info("Enhanced processing endpoints added")

# Include summarization router if available
if SUMMARIZATION_AVAILABLE:
    app.include_router(summarization_router)
    logger.info("Summarization endpoints added")

# Global variables for job tracking
# Legacy job tracking removed - use enhanced processing endpoints instead

# Pydantic models


class ProcessingStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProcessingRequest(BaseModel):
    analyzer_template: str = "content_document"
    generate_summary: bool = True
    output_dir: Optional[str] = None


class ProcessingResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "enhanced_processing_available": ENHANCED_PROCESSING_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

# Configuration endpoint


@app.get("/config")
async def get_config():
    """Get configuration status."""
    if not ENHANCED_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Enhanced processing not available")

    return {
        "azure_ai_service_endpoint": os.getenv("AZURE_AI_SERVICE_ENDPOINT") is not None,
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT") is not None,
        "content_output_directory": CONTENT_OUTPUT_DIRECTORY,
        "enhanced_processing_available": ENHANCED_PROCESSING_AVAILABLE,
        "api_version": "1.0.0"
    }

# List analyzer templates


@app.get("/analyzer-templates")
async def list_analyzer_templates():
    """List available analyzer templates."""
    templates_dir = Path("analyzer_templates")
    if not templates_dir.exists():
        return {"templates": []}

    templates = []
    for template_file in templates_dir.glob("*.json"):
        templates.append({
            "name": template_file.stem,
            "filename": template_file.name,
            "path": str(template_file)
        })

    return {"templates": templates}

# Process PDF endpoint


# Legacy PDF processing endpoint removed - use /enhanced/process for better quality and reliability


# Legacy background processing function removed - use enhanced processing instead


# Legacy job status tracking removed - use enhanced processing endpoints instead

# Job status endpoint


# Legacy job status endpoints removed - use /enhanced/status/{job_id} and /enhanced/jobs for better functionality

# List all processed books


@app.get("/books")
async def list_books():
    """List all processed books with readable directory names."""
    base_output_dir = Path(CONTENT_OUTPUT_DIRECTORY)

    if not base_output_dir.exists():
        return {"books": []}

    books = []
    for book_dir in base_output_dir.iterdir():
        if book_dir.is_dir():
            # Parse directory name: {book_title}_{timestamp}_{job_id}
            dir_name = book_dir.name
            parts = dir_name.split('_')

            # UUID is at least 32 chars
            if len(parts) >= 3 and len(parts[-1]) >= 32:
                # New format: book_title_YYYYMMDD_HHMMSS_job_id
                job_id = parts[-1]
                timestamp_parts = parts[-3:-1]  # YYYYMMDD, HHMMSS
                timestamp = f"{timestamp_parts[0]}_{timestamp_parts[1]}"
                book_title = "_".join(parts[:-3])
                # Convert back to readable title
                book_title = book_title.replace('_', ' ')
            elif len(parts) >= 2 and len(parts[-1]) >= 32:
                # Format: book_title_job_id (older format)
                job_id = parts[-1]
                timestamp = "unknown"
                book_title = "_".join(parts[:-1])
                book_title = book_title.replace('_', ' ')
            else:
                # Old format: just job_id
                job_id = dir_name
                timestamp = "unknown"
                book_title = "Unknown Book"

            # Check if metadata exists
            metadata_file = book_dir / "metadata.json"
            created_at = None
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        import json
                        metadata = json.load(f)
                        created_at = metadata.get("processing_date")
                        # Override book title from metadata if available
                        book_title = metadata.get("book_title", book_title)
                except:
                    pass

            books.append({
                "directory_name": dir_name,
                "book_title": book_title,
                "job_id": job_id,
                "timestamp": timestamp,
                "created_at": created_at,
                "path": str(book_dir)
            })

    # Sort by creation time (newest first)
    books.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"books": books}

# Simple test endpoint


@app.post("/test-pipeline")
async def test_pipeline():
    """Test the enhanced processing pipeline with a sample document."""
    if not ENHANCED_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Enhanced processing not available")

    # Check if sample PDF exists
    sample_pdf = Path("data/sample_layout.pdf")
    if not sample_pdf.exists():
        # Try other sample files
        for pdf_file in Path("data").glob("*.pdf"):
            sample_pdf = pdf_file
            break
        else:
            raise HTTPException(
                status_code=404, detail="No sample PDF found in data/ directory")

    try:
        # Import the enhanced processing function
        from .enhanced_document_processor import process_pdf_with_notebook_quality

        # Test with enhanced processing
        result = process_pdf_with_notebook_quality(
            pdf_path=str(sample_pdf),
            output_dir="test_output",
            analyzer_template_path="analyzer_templates/image_chart_diagram_understanding.json",
            custom_filename="test_document",
            use_content_books_structure=True,
            content_type="book"
        )

        return {
            "status": "success",
            "message": "Enhanced pipeline test completed successfully",
            "sample_file": str(sample_pdf),
            "result": {
                "processing_status": "completed",
                "enhanced_markdown_length": len(result.get("enhanced_markdown", "")),
                "figures_processed": result.get("figures_processed", 0),
                "main_folder": result.get("main_folder"),
                "book_title": result.get("book_title"),
                "metadata_file": result.get("metadata_file")
            }
        }

    except Exception as e:
        logger.error(f"Enhanced pipeline test failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Enhanced pipeline test failed: {e}")

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Educational Content Understanding API",
        "version": "1.0.0",
        "description": "API for processing educational documents with Azure Content Understanding",
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "analyzer_templates": "/analyzer-templates",
            "enhanced_processing": "/enhanced/process",
            "enhanced_status": "/enhanced/status/{job_id}",
            "enhanced_download": "/enhanced/download/{job_id}/{file_type}",
            "test_pipeline": "/test-pipeline"
        },
        "enhanced_processing_available": ENHANCED_PROCESSING_AVAILABLE
    }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Educational Content Understanding API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to bind to")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    print(f"🚀 Starting Educational Content Understanding API Server")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔧 Enhanced Processing Available: {ENHANCED_PROCESSING_AVAILABLE}")

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
