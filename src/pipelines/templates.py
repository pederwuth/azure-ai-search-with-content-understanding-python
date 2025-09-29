"""
Pipeline Templates

Pre-built pipeline configurations for common workflows.
"""

import logging
from typing import Dict, List, Optional, Any

from ..tasks.models import PipelineConfig, TaskConfig

logger = logging.getLogger(__name__)


def get_pipeline_templates() -> Dict[str, PipelineConfig]:
    """
    Get all available pipeline templates

    Returns:
        Dict[str, PipelineConfig]: Dictionary of template name to pipeline config
    """
    return {
        "document_to_summary": _create_document_to_summary_pipeline(),
        "complete_book_processing": _create_complete_book_processing_pipeline(),
        "document_processing_only": _create_document_processing_only_pipeline(),
        "summarization_only": _create_summarization_only_pipeline(),
    }


def create_pipeline_from_template(template_name: str, **kwargs) -> PipelineConfig:
    """
    Create a pipeline from a template with customizations

    Args:
        template_name: Name of the template to use
        **kwargs: Template-specific parameters

    Returns:
        PipelineConfig: Configured pipeline

    Raises:
        ValueError: If template is not found
    """
    templates = get_pipeline_templates()

    if template_name not in templates:
        available = list(templates.keys())
        raise ValueError(
            f"Template '{template_name}' not found. Available: {available}")

    config = templates[template_name]

    # Apply customizations based on kwargs
    if kwargs:
        # Create a copy of the config with modifications
        new_tasks = []
        for task in config.tasks:
            new_task = TaskConfig(
                task_id=task.task_id,
                inputs=dict(task.inputs),
                settings=dict(task.settings)
            )

            # Apply customizations
            if task.task_id in kwargs:
                task_params = kwargs[task.task_id]
                if isinstance(task_params, dict):
                    new_task.inputs.update(task_params.get('inputs', {}))
                    new_task.settings.update(task_params.get('settings', {}))

            new_tasks.append(new_task)

        config = PipelineConfig(
            name=config.name,
            description=config.description,
            tasks=new_tasks,
            settings=dict(config.settings),
            metadata=dict(config.metadata)
        )

        # Apply global settings
        if 'settings' in kwargs:
            config.settings.update(kwargs['settings'])
        if 'metadata' in kwargs:
            config.metadata.update(kwargs['metadata'])

    return config


def _create_document_to_summary_pipeline() -> PipelineConfig:
    """Create pipeline that processes PDF to enhanced markdown and then summarizes it"""
    return PipelineConfig(
        name="Document to Summary",
        description="Process PDF document with content understanding and generate book summary",
        tasks=[
            TaskConfig(
                task_id="document_processing",
                inputs={},
                settings={
                    "analyzer_template": "analyzer_templates/image_chart_diagram_understanding.json",
                    "use_content_books_structure": True,
                    "content_type": "book"
                }
            ),
            TaskConfig(
                task_id="summarization",
                inputs={
                    "enhanced_markdown": "$enhanced_markdown",  # Reference to previous task output
                    "book_title": "$book_title",
                    "main_folder": "$main_folder"  # Reference to document processing output folder
                },
                settings={}
            )
        ],
        settings={
            "output_format": "structured",
            "save_intermediates": True
        },
        metadata={
            "template_version": "1.0.0",
            "category": "document_processing",
            "estimated_duration_minutes": 25
        }
    )


def _create_complete_book_processing_pipeline() -> PipelineConfig:
    """Create comprehensive pipeline for complete book processing (future extensible)"""
    return PipelineConfig(
        name="Complete Book Processing",
        description="Full educational content pipeline: PDF → Enhanced Markdown → Summary → Learning Materials",
        tasks=[
            TaskConfig(
                task_id="document_processing",
                inputs={},
                settings={
                    "analyzer_template": "analyzer_templates/image_chart_diagram_understanding.json",
                    "use_content_books_structure": True,
                    "content_type": "book"
                }
            ),
            TaskConfig(
                task_id="summarization",
                inputs={
                    "enhanced_markdown": "$enhanced_markdown",
                    "book_title": "$book_title",
                    "main_folder": "$main_folder"  # Reference to document processing output folder
                },
                settings={}
            )
            # Future tasks will be added here as they are implemented:
            # TaskConfig(
            #     task_id="flashcard_generation",
            #     inputs={
            #         "book_summary": "$book_summary",
            #         "enhanced_markdown": "$enhanced_markdown"
            #     },
            #     settings={}
            # ),
            # TaskConfig(
            #     task_id="quiz_generation",
            #     inputs={
            #         "book_summary": "$book_summary",
            #         "enhanced_markdown": "$enhanced_markdown"
            #     },
            #     settings={}
            # ),
            # TaskConfig(
            #     task_id="learning_objectives",
            #     inputs={
            #         "book_summary": "$book_summary",
            #         "enhanced_markdown": "$enhanced_markdown"
            #     },
            #     settings={}
            # )
        ],
        settings={
            "output_format": "comprehensive",
            "save_intermediates": True,
            "generate_learning_materials": True
        },
        metadata={
            "template_version": "1.0.0",
            "category": "complete_processing",
            "estimated_duration_minutes": 45
        }
    )


def _create_document_processing_only_pipeline() -> PipelineConfig:
    """Create pipeline for document processing only"""
    return PipelineConfig(
        name="Document Processing Only",
        description="Process PDF document with enhanced content understanding (no summarization)",
        tasks=[
            TaskConfig(
                task_id="document_processing",
                inputs={},
                settings={
                    "analyzer_template": "analyzer_templates/image_chart_diagram_understanding.json",
                    "use_content_books_structure": True,
                    "content_type": "book"
                }
            )
        ],
        settings={
            "output_format": "enhanced_markdown",
            "save_intermediates": True
        },
        metadata={
            "template_version": "1.0.0",
            "category": "document_processing",
            "estimated_duration_minutes": 15
        }
    )


def _create_summarization_only_pipeline() -> PipelineConfig:
    """Create pipeline for summarization only"""
    return PipelineConfig(
        name="Summarization Only",
        description="Generate book summary from existing markdown content",
        tasks=[
            TaskConfig(
                task_id="summarization",
                inputs={},
                settings={}
            )
        ],
        settings={
            "output_format": "summary",
            "save_intermediates": True
        },
        metadata={
            "template_version": "1.0.0",
            "category": "summarization",
            "estimated_duration_minutes": 10
        }
    )


def list_template_info() -> List[Dict[str, Any]]:
    """
    Get information about all available templates

    Returns:
        List[Dict]: List of template information
    """
    templates = get_pipeline_templates()

    template_info = []
    for name, config in templates.items():
        info = {
            "name": name,
            "display_name": config.name,
            "description": config.description,
            "tasks": [task.task_id for task in config.tasks],
            "estimated_duration_minutes": config.metadata.get("estimated_duration_minutes"),
            "category": config.metadata.get("category"),
            "template_version": config.metadata.get("template_version")
        }
        template_info.append(info)

    return template_info
