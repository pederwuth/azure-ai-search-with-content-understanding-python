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
from typing import Optional, List, Dict, Any
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Environment configuration
CONTENT_OUTPUT_DIRECTORY = os.getenv("CONTENT_OUTPUT_DIRECTORY", "content/books")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our pipeline components
try:
    from src.pipeline import ContentUnderstandingPipeline, process_pdf_with_content_understanding
    from src.core.config import Settings
    from src.core.exceptions import PipelineError, ContentUnderstandingError
    PIPELINE_AVAILABLE = True
    logger.info("Content Understanding pipeline imported successfully")
except ImportError as e:
    logger.error(f"Failed to import pipeline components: {e}")
    PIPELINE_AVAILABLE = False

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

# Global variables for job tracking
processing_jobs: Dict[str, Dict[str, Any]] = {}

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
        "pipeline_available": PIPELINE_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration status."""
    if not PIPELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline not available")
    
    try:
        settings = Settings()
        config_status = {
            "azure_ai_service_configured": bool(settings.azure_ai_service_endpoint),
            "openai_configured": bool(settings.azure_openai_endpoint),
            "document_intelligence_configured": bool(settings.azure_document_intelligence_api_version),
            "content_understanding_configured": bool(settings.azure_ai_service_api_version),
        }
        return {
            "configuration": config_status,
            "all_configured": all(config_status.values())
        }
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")

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
@app.post("/process-pdf", response_model=ProcessingResponse)
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analyzer_template: str = Form("content_document"),
    generate_summary: bool = Form(True)
):
    """
    Process a PDF file with Content Understanding.
    
    Returns a job ID for tracking processing status.
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline not available")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job tracking entry
    # Use environment variable for output directory with job-specific subdirectory
    job_output_dir = f"{CONTENT_OUTPUT_DIRECTORY}/{job_id}"
    
    processing_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job created, waiting to start processing",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "filename": file.filename,
        "analyzer_template": analyzer_template,
        "generate_summary": generate_summary,
        "output_dir": job_output_dir
    }
    
    # Read file content before starting background task
    file_content = await file.read()
    
    # Start background processing
    background_tasks.add_task(
        process_pdf_background,
        job_id,
        file_content,
        file.filename or "document.pdf",
        analyzer_template,
        generate_summary,
        job_output_dir
    )
    
    logger.info(f"Created processing job {job_id} for file {file.filename}")
    
    return ProcessingResponse(
        job_id=job_id,
        status="pending",
        message="Processing job created successfully"
    )

async def process_pdf_background(
    job_id: str,
    file_content: bytes,
    filename: str,
    analyzer_template: str,
    generate_summary: bool,
    output_dir: str
):
    """Background task for processing PDF files."""
    try:
        # Update job status
        update_job_status(job_id, "processing", 10, "Starting PDF processing")
        
        # Create job directory structure
        job_dir = Path(output_dir)
        input_dir = job_dir / "input"
        processed_dir = job_dir / "processed"
        figures_dir = job_dir / "figures"
        
        # Create directories
        for dir_path in [input_dir, processed_dir, figures_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract book title from filename (remove extension and clean up)
        book_title = Path(filename).stem
        # Clean title for filesystem (remove/replace problematic characters)
        book_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        book_title = book_title.replace(' ', '_')
        
        # Create unique base filename
        unique_filename = f"{book_title}_{timestamp}"
        
        # Save original PDF to input directory
        original_pdf_path = input_dir / f"{unique_filename}.pdf"
        with open(original_pdf_path, 'wb') as f:
            f.write(file_content)
        
        # Save uploaded file content to temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_pdf_path = temp_file.name
        
        update_job_status(job_id, "processing", 20, "File saved, initializing pipeline")
        
        try:
            # Process with our pipeline
            logger.info(f"Processing {filename} with analyzer template {analyzer_template}")
            
            update_job_status(job_id, "processing", 30, "Processing with Content Understanding")
            
            # Use the job directory for Content Understanding processing (not processed subdirectory)
            logger.info(f"DEBUG: Calling process_pdf_with_content_understanding with output_dir={str(job_dir)}")
            logger.info(f"DEBUG: job_dir value = {job_dir}")
            logger.info(f"DEBUG: output_dir parameter passed to background function = {output_dir}")
            result = process_pdf_with_content_understanding(
                pdf_path=temp_pdf_path,
                output_dir=str(job_dir),  # Use the main job directory
                analyzer_template=analyzer_template,
                generate_summary=generate_summary
            )
            
            update_job_status(job_id, "processing", 70, "Processing completed, organizing files")
            
            # Save markdown file with unique naming
            markdown_content = result.get("enhanced_markdown_content", "")
            if markdown_content:
                markdown_file = processed_dir / f"{unique_filename}_enhanced.md"
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                result["enhanced_markdown_path"] = str(markdown_file)
                logger.info(f"Markdown saved to: {markdown_file}")
            
            # Create summary file with unique naming
            if generate_summary:
                summary_file = processed_dir / f"{unique_filename}_summary.json"
                
                if "book_summary" in result:
                    # Summary was generated successfully
                    logger.info(f"Summary file available at: {summary_file}")
                else:
                    # Create a basic summary with document info
                    basic_summary = {
                        "document_name": filename,
                        "book_title": book_title,
                        "processing_date": datetime.now().isoformat(),
                        "job_id": job_id,
                        "unique_filename": unique_filename,
                        "status": "summary_generation_skipped",
                        "reason": "OpenAI client not available",
                        "file_paths": {
                            "original_pdf": str(original_pdf_path),
                            "enhanced_markdown": str(markdown_file) if markdown_content else None,
                            "figures_directory": str(figures_dir)
                        },
                        "document_stats": {
                            "markdown_length": len(markdown_content),
                            "estimated_tokens": len(markdown_content.split()) * 1.3 if markdown_content else 0
                        },
                        "content_preview": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content
                    }
                    
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(basic_summary, f, indent=2)
                    
                    result["summary_file_path"] = str(summary_file)
                    result["summary_status"] = "basic_info_created"
                    logger.info(f"Basic summary info saved to: {summary_file}")
            
            # Create metadata file
            metadata = {
                "job_id": job_id,
                "original_filename": filename,
                "book_title": book_title,
                "unique_filename": unique_filename,
                "processing_date": datetime.now().isoformat(),
                "analyzer_template": analyzer_template,
                "file_structure": {
                    "input_dir": str(input_dir),
                    "processed_dir": str(processed_dir),
                    "figures_dir": str(figures_dir)
                },
                "files": {
                    "original_pdf": str(original_pdf_path),
                    "enhanced_markdown": str(markdown_file) if markdown_content else None,
                    "summary": str(summary_file) if generate_summary else None
                }
            }
            
            metadata_file = job_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Job metadata saved to: {metadata_file}")
            
            update_job_status(job_id, "processing", 90, "Processing completed, saving results")
            
            # Clean up temporary file
            os.unlink(temp_pdf_path)
            
            # Update job with results
            processing_jobs[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Processing completed successfully",
                "updated_at": datetime.now(),
                "result": result
            })
            
            logger.info(f"Successfully processed job {job_id}")
            
        finally:
            # Ensure temp file is cleaned up
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
    
    except Exception as e:
        logger.error(f"Processing failed for job {job_id}: {e}")
        processing_jobs[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Processing failed: {str(e)}",
            "updated_at": datetime.now(),
            "error": str(e)
        })

def update_job_status(job_id: str, status: str, progress: int, message: str):
    """Update job status."""
    if job_id in processing_jobs:
        processing_jobs[job_id].update({
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": datetime.now()
        })
        logger.info(f"Job {job_id}: {status} - {progress}% - {message}")

# Job status endpoint
@app.get("/jobs/{job_id}", response_model=ProcessingStatus)
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = processing_jobs[job_id]
    return ProcessingStatus(**job_data)

# List all jobs
@app.get("/jobs")
async def list_jobs():
    """List all processing jobs."""
    jobs = []
    for job_data in processing_jobs.values():
        jobs.append({
            "job_id": job_data["job_id"],
            "status": job_data["status"],
            "progress": job_data["progress"],
            "message": job_data["message"],
            "created_at": job_data["created_at"],
            "filename": job_data.get("filename", ""),
            "analyzer_template": job_data.get("analyzer_template", "")
        })
    
    # Sort by creation time, newest first
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return {"jobs": jobs}

# Download results endpoint
@app.get("/jobs/{job_id}/download/{file_type}")
async def download_result(job_id: str, file_type: str):
    """Download processing results."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = processing_jobs[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    result = job_data.get("result")
    if not result:
        raise HTTPException(status_code=404, detail="No results available")
    
    # Handle different file types
    if file_type == "pdf":
        # Download original PDF
        job_dir = Path(f"content/books/{job_id}")
        metadata_file = job_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                import json
                metadata = json.load(f)
            original_pdf = metadata.get("files", {}).get("original_pdf")
            if original_pdf and os.path.exists(original_pdf):
                return FileResponse(
                    original_pdf,
                    media_type="application/pdf",
                    filename=f"original_{job_data['filename']}"
                )
    
    elif file_type == "markdown" and "enhanced_markdown_path" in result:
        file_path = result["enhanced_markdown_path"]
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="text/markdown",
                filename=f"enhanced_{job_data['filename']}.md"
            )
    
    elif file_type == "summary" and "summary_file_path" in result:
        file_path = result["summary_file_path"]
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="application/json",
                filename=f"summary_{job_data['filename']}.json"
            )
    
    elif file_type == "metadata":
        # Download job metadata
        job_dir = Path(f"content/books/{job_id}")
        metadata_file = job_dir / "metadata.json"
        if metadata_file.exists():
            return FileResponse(
                str(metadata_file),
                media_type="application/json",
                filename=f"metadata_{job_id}.json"
            )
    
    raise HTTPException(status_code=404, detail=f"File type '{file_type}' not available")

# Simple test endpoint
@app.post("/test-pipeline")
async def test_pipeline():
    """Test the pipeline with a sample document."""
    if not PIPELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline not available")
    
    # Check if sample PDF exists
    sample_pdf = Path("data/sample_layout.pdf")
    if not sample_pdf.exists():
        # Try other sample files
        for pdf_file in Path("data").glob("*.pdf"):
            sample_pdf = pdf_file
            break
        else:
            raise HTTPException(status_code=404, detail="No sample PDF found in data/ directory")
    
    try:
        # Test with minimal processing (use the same template as the working notebook)
        result = process_pdf_with_content_understanding(
            pdf_path=str(sample_pdf),
            output_dir="test_output",
            analyzer_template="image_chart_diagram_understanding",  # Use same template as notebook
            generate_summary=False  # Skip summary for faster testing
        )
        
        return {
            "status": "success",
            "message": "Pipeline test completed successfully",
            "sample_file": str(sample_pdf),
            "result": {
                "processing_status": result.get("processing_status"),
                "enhanced_markdown_length": len(result.get("enhanced_markdown_content", "")),
                "figures_directory": result.get("figures_directory"),
                "output_files": {
                    "enhanced_markdown": result.get("enhanced_markdown_path"),
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline test failed: {e}")

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
            "process_pdf": "/process-pdf",
            "test_pipeline": "/test-pipeline",
            "jobs": "/jobs",
            "job_status": "/jobs/{job_id}",
            "download": "/jobs/{job_id}/download/{file_type}"
        },
        "pipeline_available": PIPELINE_AVAILABLE
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Educational Content Understanding API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Educational Content Understanding API Server")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔧 Pipeline Available: {PIPELINE_AVAILABLE}")
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
