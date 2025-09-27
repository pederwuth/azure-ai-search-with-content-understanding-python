"""
Pipeline System

This module provides pipeline orchestration for educational content processing tasks.
"""

from .api import router as pipeline_router
from .templates import get_pipeline_templates, create_pipeline_from_template
from .storage import PipelineStorage

__all__ = [
    'pipeline_router',
    'get_pipeline_templates',
    'create_pipeline_from_template',
    'PipelineStorage'
]
