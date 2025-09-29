"""
Pipeline API

FastAPI endpoints for pipeline orchestration and management.
"""

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..tasks.executor import PipelineExecutor
from ..tasks.models import TaskStatus, PipelineConfig, TaskConfig
from ..tasks.registry import get_task_registry
from .templates import get_pipeline_templates, create_pipeline_from_template, list_template_info
from .storage import PipelineStorage

logger = logging.getLogger(__name__)

# Create router for pipeline endpoints
router = APIRouter(tags=["Pipeline Orchestration"])

# Global pipeline storage and executor
pipeline_storage = PipelineStorage()
pipeline_executor = PipelineExecutor()

# In-memory pipeline job tracking
active_pipelines: Dict[str, Dict[str, Any]] = {}


class PipelineExecutionRequest(BaseModel):
    """Request model for custom pipeline execution"""
    name: str = Field(description="Name for this pipeline execution")
    description: str = Field(
        description="Description of what this pipeline does")
    tasks: List[str] = Field(description="List of task IDs to execute")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Global pipeline settings")


class TemplateExecutionRequest(BaseModel):
    """Request model for template-based pipeline execution"""
    custom_filename: Optional[str] = Field(
        None, description="Custom name for the book")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Pipeline settings")
    task_settings: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Per-task settings")


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status"""
    pipeline_id: str
    name: str
    description: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    current_task: Optional[str] = None
    completed_tasks: List[str] = []
    total_tasks: int
    error_message: Optional[str] = None
    final_outputs: Optional[Dict[str, Any]] = None


@router.get("/templates")
async def list_pipeline_templates():
    """List all available pipeline templates with their information"""
    return {
        "templates": list_template_info(),
        "total_count": len(list_template_info())
    }


@router.get("/templates/{template_name}")
async def get_pipeline_template(template_name: str):
    """Get detailed information about a specific pipeline template"""
    templates = get_pipeline_templates()

    if template_name not in templates:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {list(templates.keys())}"
        )

    config = templates[template_name]

    return {
        "name": template_name,
        "config": {
            "name": config.name,
            "description": config.description,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "inputs": task.inputs,
                    "settings": task.settings
                } for task in config.tasks
            ],
            "settings": config.settings,
            "metadata": config.metadata
        }
    }


@router.post("/templates/{template_name}/execute-with-path")
async def execute_pipeline_template_with_path(
    template_name: str,
    background_tasks: BackgroundTasks,
    file_path: str = Form(..., description="Path to input file on server"),
    custom_filename: Optional[str] = Form(
        None, description="Custom name for the book"),
    settings: str = Form("{}", description="Pipeline settings as JSON string")
):
    """
    Execute a pipeline using a pre-built template with a file path

    This endpoint allows you to run pipelines with files already on the server.
    Useful for testing with sample files.
    """
    import json
    from pathlib import Path

    # Parse settings
    try:
        pipeline_settings = json.loads(settings) if settings != "{}" else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON in settings parameter")

    # Validate template exists
    templates = get_pipeline_templates()
    if template_name not in templates:
        available = list(templates.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {available}"
        )

    # Validate file exists
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise HTTPException(
            status_code=400, detail=f"File not found: {file_path}")

    # Generate pipeline ID
    pipeline_id = str(uuid.uuid4())

    # Read file content
    try:
        file_content = file_path_obj.read_bytes()
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error reading file: {str(e)}")

    # Initialize pipeline tracking
    active_pipelines[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "template_name": template_name,
        "status": "starting",
        "message": f"Initializing pipeline: {template_name}",
        "filename": file_path_obj.name,
        "custom_filename": custom_filename,
        "settings": pipeline_settings,
        "start_time": "2025-09-22T00:00:00Z"
    }

    logger.info(
        f"Starting template pipeline {template_name} with ID {pipeline_id}")

    # Start background execution
    background_tasks.add_task(
        _execute_template_pipeline_background,
        pipeline_id,
        template_name,
        file_content,
        file_path_obj.name,
        custom_filename,
        pipeline_settings
    )

    return {
        "pipeline_id": pipeline_id,
        "template_name": template_name,
        "status": "starting",
        "message": f"Pipeline execution started using template: {template_name}"
    }


@router.post("/templates/{template_name}/execute")
async def execute_pipeline_template(
    template_name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Input file (usually PDF)"),
    custom_filename: Optional[str] = Form(
        default=None, description="Custom name for the book (optional)"),
    settings: str = Form(
        default="{}", description="Pipeline settings as JSON string")
):
    """
    Execute a pipeline using a pre-built template

    This endpoint allows you to run common pipeline workflows like 'document_to_summary'
    with a simple file upload.
    """
    import json

    # Parse settings
    try:
        pipeline_settings = json.loads(settings) if settings != "{}" else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON in settings parameter")

    # Validate template exists
    templates = get_pipeline_templates()
    if template_name not in templates:
        available = list(templates.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {available}"
        )

    # Generate pipeline ID
    pipeline_id = str(uuid.uuid4())

    # Read file content
    file_content = await file.read()

    # Initialize pipeline tracking
    active_pipelines[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "template_name": template_name,
        "status": "starting",
        "message": f"Initializing pipeline: {template_name}",
        "filename": file.filename,
        "custom_filename": custom_filename,
        "start_time": "2025-09-22T00:00:00Z"  # Will be updated in background task
    }

    logger.info(
        f"Starting template pipeline {template_name} with ID {pipeline_id}")

    # Start background execution
    background_tasks.add_task(
        _execute_template_pipeline_background,
        pipeline_id,
        template_name,
        file_content,
        file.filename,
        custom_filename,
        pipeline_settings
    )

    return {
        "pipeline_id": pipeline_id,
        "template_name": template_name,
        "status": "starting",
        "message": f"Pipeline execution started using template: {template_name}"
    }


@router.post("/execute", response_model=Dict[str, str])
async def execute_custom_pipeline(
    request: PipelineExecutionRequest,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Input file for the pipeline")
):
    """
    Execute a custom pipeline with specified tasks

    This endpoint allows you to create and execute custom task sequences.
    """
    # Generate pipeline ID
    pipeline_id = str(uuid.uuid4())

    # Read file content
    file_content = await file.read()

    # Validate tasks exist
    registry = get_task_registry()
    for task_id in request.tasks:
        if task_id not in registry.list_tasks():
            available = registry.list_tasks()
            raise HTTPException(
                status_code=400,
                detail=f"Task '{task_id}' not found. Available: {available}"
            )

    # Initialize pipeline tracking
    active_pipelines[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "status": "starting",
        "message": f"Initializing custom pipeline: {request.name}",
        "filename": file.filename,
        "tasks": request.tasks,
        "start_time": "2025-09-22T00:00:00Z"
    }

    logger.info(
        f"Starting custom pipeline {request.name} with ID {pipeline_id}")

    # Start background execution
    background_tasks.add_task(
        _execute_custom_pipeline_background,
        pipeline_id,
        request,
        file_content,
        file.filename
    )

    return {
        "pipeline_id": pipeline_id,
        "status": "starting",
        "message": f"Custom pipeline execution started: {request.name}"
    }


@router.get("/status/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str):
    """Get the status of a pipeline execution"""

    # Check active pipelines first
    if pipeline_id in active_pipelines:
        pipeline_info = active_pipelines[pipeline_id]

        return PipelineStatusResponse(
            pipeline_id=pipeline_id,
            name=pipeline_info.get("name", "Pipeline"),
            description=pipeline_info.get("description", ""),
            status=pipeline_info["status"],
            start_time=pipeline_info["start_time"],
            end_time=pipeline_info.get("end_time"),
            duration_seconds=pipeline_info.get("duration_seconds"),
            current_task=pipeline_info.get("current_task"),
            completed_tasks=pipeline_info.get("completed_tasks", []),
            total_tasks=pipeline_info.get("total_tasks", 0),
            error_message=pipeline_info.get("error_message"),
            final_outputs=pipeline_info.get("final_outputs")
        )

    # Check stored results
    stored_result = pipeline_storage.load_pipeline_result(pipeline_id)
    if stored_result:
        completed_tasks = [
            task_id for task_id, execution in stored_result.task_executions.items()
            if execution.status == TaskStatus.COMPLETED
        ]

        return PipelineStatusResponse(
            pipeline_id=pipeline_id,
            name=stored_result.config.name,
            description=stored_result.config.description,
            status=stored_result.status.value,
            start_time=stored_result.start_time.isoformat(),
            end_time=stored_result.end_time.isoformat() if stored_result.end_time else None,
            duration_seconds=stored_result.duration_seconds,
            completed_tasks=completed_tasks,
            total_tasks=len(stored_result.config.tasks),
            error_message=stored_result.error_message,
            final_outputs=stored_result.final_outputs.data if stored_result.final_outputs else None
        )

    raise HTTPException(status_code=404, detail="Pipeline not found")


@router.get("/list")
async def list_pipelines(status: Optional[str] = None, limit: Optional[int] = 20):
    """List pipeline executions"""

    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in TaskStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid: {valid_statuses}"
            )

    # Get stored pipelines
    stored_pipelines = pipeline_storage.list_pipelines(status_filter, limit)

    # Add active pipelines
    active_list = []
    for pipeline_id, info in active_pipelines.items():
        if not status_filter or info["status"] == status_filter.value:
            active_list.append({
                "pipeline_id": pipeline_id,
                "name": info.get("name", "Active Pipeline"),
                "status": info["status"],
                "start_time": info["start_time"],
                "template_name": info.get("template_name")
            })

    return {
        "active_pipelines": active_list,
        "stored_pipelines": stored_pipelines,
        "total_active": len(active_list),
        "total_stored": len(stored_pipelines)
    }


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """Delete a pipeline and its results"""

    # Remove from active if present
    if pipeline_id in active_pipelines:
        del active_pipelines[pipeline_id]

    # Delete stored results
    success = pipeline_storage.delete_pipeline(pipeline_id)

    if success:
        return {"message": f"Pipeline {pipeline_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Pipeline not found")


@router.get("/tasks")
async def list_available_tasks():
    """List all available tasks that can be used in pipelines"""
    registry = get_task_registry()

    task_info = []
    for task_id in registry.list_tasks():
        try:
            info = registry.get_task_info(task_id)
            task_info.append(info)
        except Exception as e:
            logger.warning(f"Could not get info for task {task_id}: {e}")

    return {
        "tasks": task_info,
        "total_count": len(task_info)
    }


# Background task functions

async def _execute_template_pipeline_background(
    pipeline_id: str,
    template_name: str,
    file_content: bytes,
    filename: str,
    custom_filename: Optional[str],
    settings: Dict[str, Any]
):
    """Background task for template pipeline execution"""
    try:
        from datetime import datetime

        # Update status
        active_pipelines[pipeline_id].update({
            "status": "running",
            "message": f"Executing template pipeline: {template_name}",
            "start_time": datetime.now().isoformat()
        })

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_pdf_path = temp_file.name

        try:
            # Create pipeline from template
            config = create_pipeline_from_template(template_name, **settings)

            # Prepare initial inputs
            # Debug logging to see what filename we received
            logger.info(
                f"🔍 Filename received: '{filename}', Custom filename: '{custom_filename}'")

            # Filter out Swagger UI placeholder values
            swagger_placeholders = {"string", "str",
                                    "text", "filename", "name", "title"}
            if custom_filename and custom_filename.lower().strip() in swagger_placeholders:
                logger.info(
                    f"🚫 Ignoring Swagger UI placeholder value: '{custom_filename}'")
                custom_filename = None

            # Use custom_filename as original_filename if provided and filename looks temporary
            effective_filename = filename
            if custom_filename and (not filename or filename.startswith('tmp') or '.' not in filename):
                effective_filename = custom_filename if custom_filename.endswith(
                    '.pdf') else f"{custom_filename}.pdf"
                logger.info(
                    f"🔄 Using custom_filename as effective filename: '{effective_filename}'")

            initial_inputs = {
                "pdf": temp_pdf_path,
                "pdf_file": temp_pdf_path,
                "original_filename": effective_filename
            }

            if custom_filename:
                initial_inputs["custom_filename"] = custom_filename

            # Execute pipeline
            result = await pipeline_executor.execute_pipeline(
                config,
                initial_inputs,
                pipeline_id
            )

            # Save result
            pipeline_storage.save_pipeline_result(result)

            # Update tracking
            active_pipelines[pipeline_id].update({
                "status": result.status.value,
                "message": "Pipeline execution completed" if result.status == TaskStatus.COMPLETED else f"Pipeline failed: {result.error_message}",
                "end_time": datetime.now().isoformat(),
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
                "final_outputs": result.final_outputs.data if result.final_outputs else None
            })

            logger.info(
                f"Template pipeline {template_name} completed: {pipeline_id}")

        finally:
            # Clean up temp file
            Path(temp_pdf_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Template pipeline {template_name} failed: {e}")
        active_pipelines[pipeline_id].update({
            "status": "failed",
            "message": f"Pipeline execution failed: {str(e)}",
            "error_message": str(e),
            "end_time": datetime.now().isoformat()
        })


async def _execute_custom_pipeline_background(
    pipeline_id: str,
    request: PipelineExecutionRequest,
    file_content: bytes,
    filename: str
):
    """Background task for custom pipeline execution"""
    try:
        from datetime import datetime

        # Update status
        active_pipelines[pipeline_id].update({
            "status": "running",
            "message": f"Executing custom pipeline: {request.name}",
            "start_time": datetime.now().isoformat(),
            "name": request.name,
            "description": request.description,
            "total_tasks": len(request.tasks)
        })

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_pdf_path = temp_file.name

        try:
            # Create pipeline config
            config = PipelineConfig(
                name=request.name,
                description=request.description,
                tasks=[TaskConfig(task_id=task_id)
                       for task_id in request.tasks],
                settings=request.settings
            )

            # Prepare initial inputs
            initial_inputs = {
                "pdf": temp_pdf_path,
                "pdf_file": temp_pdf_path,
                "original_filename": filename
            }

            # Execute pipeline
            result = await pipeline_executor.execute_pipeline(
                config,
                initial_inputs,
                pipeline_id
            )

            # Save result
            pipeline_storage.save_pipeline_result(result)

            # Update tracking
            active_pipelines[pipeline_id].update({
                "status": result.status.value,
                "message": "Pipeline execution completed" if result.status == TaskStatus.COMPLETED else f"Pipeline failed: {result.error_message}",
                "end_time": datetime.now().isoformat(),
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
                "final_outputs": result.final_outputs.data if result.final_outputs else None
            })

            logger.info(
                f"Custom pipeline {request.name} completed: {pipeline_id}")

        finally:
            # Clean up temp file
            Path(temp_pdf_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Custom pipeline {request.name} failed: {e}")
        active_pipelines[pipeline_id].update({
            "status": "failed",
            "message": f"Pipeline execution failed: {str(e)}",
            "error_message": str(e),
            "end_time": datetime.now().isoformat()
        })
