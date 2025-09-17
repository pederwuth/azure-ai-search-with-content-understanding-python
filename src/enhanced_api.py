"""
FastAPI endpoint for Enhanced Document Processing.

This module provides API endpoints that use the enhanced document processor
to deliver the same high-quality output as the notebook approach.
"""

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .enhanced_document_processor import process_pdf_with_notebook_quality

logger = logging.getLogger(__name__)

# Create router for enhanced processing endpoints
router = APIRouter(prefix="/enhanced", tags=["Enhanced Processing"])


class EnhancedProcessingRequest(BaseModel):
    """Request model for enhanced document processing."""
    custom_filename: Optional[str] = None
    analyzer_template: str = "analyzer_templates/image_chart_diagram_understanding.json"


class EnhancedProcessingResponse(BaseModel):
    """Response model for enhanced document processing."""
    job_id: str
    status: str
    message: str
    pdf_file: Optional[str] = None
    enhanced_markdown: Optional[str] = None
    cache_file: Optional[str] = None
    figures_directory: Optional[str] = None
    figures_processed: Optional[int] = None
    document_length: Optional[int] = None
    processing_stats: Optional[Dict[str, Any]] = None


# In-memory job storage for enhanced processing
enhanced_jobs = {}


@router.post("/process", response_model=EnhancedProcessingResponse)
async def process_pdf_enhanced(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    custom_filename: Optional[str] = Form(None),
    analyzer_template: str = Form(
        "analyzer_templates/image_chart_diagram_understanding.json")
):
    """
    Process a PDF file with enhanced content understanding (notebook quality).

    This endpoint provides the same high-quality processing as the notebook
    'search_with_visual_document.ipynb' with rich content understanding analysis.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Initialize job
    enhanced_jobs[job_id] = {
        "status": "processing",
        "message": "Enhanced document processing started",
        "filename": file.filename,
        "created_at": "2025-01-16T23:52:00Z"  # Current timestamp
    }

    logger.info(
        f"Started enhanced processing job {job_id} for file: {file.filename}")

    # Start background processing
    background_tasks.add_task(
        _process_pdf_enhanced_background,
        job_id,
        file,
        custom_filename,
        analyzer_template
    )

    return EnhancedProcessingResponse(
        job_id=job_id,
        status="processing",
        message="Enhanced document processing started"
    )


async def _process_pdf_enhanced_background(
    job_id: str,
    file: UploadFile,
    custom_filename: Optional[str],
    analyzer_template: str
):
    """Background task for enhanced PDF processing."""
    try:
        # Update job status
        enhanced_jobs[job_id]["status"] = "processing"
        enhanced_jobs[job_id]["message"] = "Analyzing document with enhanced content understanding..."

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_pdf_path = temp_file.name

        try:
            # Create output directory
            output_dir = Path("content/enhanced") / f"enhanced_{job_id}"

            # Process with enhanced understanding
            logger.info(
                f"Processing {file.filename} with enhanced content understanding...")

            results = process_pdf_with_notebook_quality(
                pdf_path=temp_pdf_path,
                output_dir=output_dir,
                analyzer_template_path=analyzer_template,
                custom_filename=custom_filename
            )

            # Update job with results
            enhanced_jobs[job_id].update({
                "status": "completed",
                "message": "Enhanced document processing completed successfully",
                "results": results,
                "pdf_file": results["pdf_file"],
                "enhanced_markdown": results["enhanced_markdown"],
                "cache_file": results["cache_file"],
                "figures_directory": results["figures_directory"],
                "figures_processed": results["figures_processed"],
                "document_length": results["document_length"],
                "processing_stats": results["processing_stats"]
            })

            logger.info(f"Enhanced processing completed for job {job_id}")
            logger.info(f"Figures processed: {results['figures_processed']}")
            logger.info(
                f"Document length: {results['document_length']:,} characters")

        finally:
            # Clean up temporary file
            Path(temp_pdf_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Enhanced processing failed for job {job_id}: {e}")
        enhanced_jobs[job_id].update({
            "status": "failed",
            "message": f"Enhanced processing failed: {str(e)}",
            "error": str(e)
        })


@router.get("/status/{job_id}", response_model=EnhancedProcessingResponse)
async def get_enhanced_job_status(job_id: str):
    """Get the status of an enhanced processing job."""
    if job_id not in enhanced_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = enhanced_jobs[job_id]

    return EnhancedProcessingResponse(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        pdf_file=job.get("pdf_file"),
        enhanced_markdown=job.get("enhanced_markdown"),
        cache_file=job.get("cache_file"),
        figures_directory=job.get("figures_directory"),
        figures_processed=job.get("figures_processed"),
        document_length=job.get("document_length"),
        processing_stats=job.get("processing_stats")
    )


@router.get("/download/{job_id}/markdown")
async def download_enhanced_markdown(job_id: str):
    """Download the enhanced markdown file for a completed job."""
    if job_id not in enhanced_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = enhanced_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    markdown_path = job.get("enhanced_markdown")
    if not markdown_path or not Path(markdown_path).exists():
        raise HTTPException(
            status_code=404, detail="Enhanced markdown file not found")

    return FileResponse(
        markdown_path,
        media_type="text/markdown",
        filename=f"enhanced_{Path(markdown_path).name}"
    )


@router.get("/download/{job_id}/cache")
async def download_enhanced_cache(job_id: str):
    """Download the cache file for a completed job."""
    if job_id not in enhanced_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = enhanced_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    cache_path = job.get("cache_file")
    if not cache_path or not Path(cache_path).exists():
        raise HTTPException(status_code=404, detail="Cache file not found")

    return FileResponse(
        cache_path,
        media_type="application/json",
        filename=f"cache_{Path(cache_path).name}"
    )


@router.delete("/jobs/{job_id}")
async def delete_enhanced_job(job_id: str):
    """Delete an enhanced processing job and its files."""
    if job_id not in enhanced_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = enhanced_jobs[job_id]

    # Clean up files if they exist
    files_to_clean = ["enhanced_markdown", "cache_file"]
    for file_key in files_to_clean:
        file_path = job.get(file_key)
        if file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete {file_path}: {e}")

    # Clean up figures directory
    figures_dir = job.get("figures_directory")
    if figures_dir:
        try:
            figures_path = Path(figures_dir)
            if figures_path.exists():
                for figure_file in figures_path.glob("*.png"):
                    figure_file.unlink(missing_ok=True)
                figures_path.rmdir()
        except Exception as e:
            logger.warning(
                f"Could not clean up figures directory {figures_dir}: {e}")

    # Remove job from memory
    del enhanced_jobs[job_id]

    return {"message": f"Enhanced job {job_id} deleted successfully"}


@router.get("/jobs")
async def list_enhanced_jobs():
    """List all enhanced processing jobs."""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "message": job["message"],
                "filename": job.get("filename"),
                "created_at": job.get("created_at"),
                "figures_processed": job.get("figures_processed"),
                "document_length": job.get("document_length")
            }
            for job_id, job in enhanced_jobs.items()
        ]
    }
