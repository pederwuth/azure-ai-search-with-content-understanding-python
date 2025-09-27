"""
Task System for Educational Content Processing

This module provides a pipeline-based architecture for educational content processing
that allows tasks to be executed individually or chained together.
"""

from .base import BaseTask, TaskInputs, TaskOutputs, TaskConfig
from .registry import TaskRegistry, get_task_registry
from .executor import PipelineExecutor, PipelineResult
from .models import TaskMetadata, PipelineConfig, TaskStatus

__all__ = [
    'BaseTask',
    'TaskInputs',
    'TaskOutputs',
    'TaskConfig',
    'TaskRegistry',
    'get_task_registry',
    'PipelineExecutor',
    'PipelineResult',
    'TaskMetadata',
    'PipelineConfig',
    'TaskStatus'
]
