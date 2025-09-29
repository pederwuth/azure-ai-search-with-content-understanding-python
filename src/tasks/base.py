"""
Base Task Interface

Defines the interface that all tasks must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .models import TaskInputs, TaskOutputs, TaskMetadata, TaskInputType, TaskOutputType

logger = logging.getLogger(__name__)


class BaseTask(ABC):
    """Base class for all processing tasks"""

    def __init__(self):
        """Initialize the task"""
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def metadata(self) -> TaskMetadata:
        """Get task metadata"""
        pass

    @property
    def task_id(self) -> str:
        """Get task identifier"""
        return self.metadata.task_id

    @property
    def input_types(self) -> List[TaskInputType]:
        """Get input types this task accepts"""
        return self.metadata.input_types

    @property
    def output_types(self) -> List[TaskOutputType]:
        """Get output types this task produces"""
        return self.metadata.output_types

    @property
    def dependencies(self) -> List[str]:
        """Get task dependencies"""
        return self.metadata.dependencies

    @abstractmethod
    async def execute(self, inputs: TaskInputs) -> TaskOutputs:
        """
        Execute the task with given inputs

        Args:
            inputs: Task inputs containing data, files, and metadata

        Returns:
            TaskOutputs: Results of task execution

        Raises:
            Exception: If task execution fails
        """
        pass

    def can_process(self, available_outputs: Dict[str, Any]) -> bool:
        """
        Check if this task can run with available outputs from previous tasks

        Args:
            available_outputs: Outputs available from previous tasks

        Returns:
            bool: True if task can run with available outputs
        """
        # Check if any of our required input types are available
        for input_type in self.input_types:
            if input_type.value in available_outputs:
                return True
        return False

    def validate_inputs(self, inputs: TaskInputs) -> bool:
        """
        Validate that inputs are sufficient for task execution

        Args:
            inputs: Task inputs to validate

        Returns:
            bool: True if inputs are valid
        """
        # Basic validation - check if we have at least one required input type
        has_required_input = False
        for input_type in self.input_types:
            if (input_type.value in inputs.data or
                    input_type.value in inputs.files):
                has_required_input = True
                break

        return has_required_input

    async def setup(self) -> None:
        """
        Setup task before execution (optional override)
        Called before execute()
        """
        pass

    async def cleanup(self) -> None:
        """
        Cleanup after task execution (optional override)
        Called after execute() regardless of success/failure
        """
        pass

    def __str__(self) -> str:
        """String representation of task"""
        return f"{self.__class__.__name__}(id={self.task_id})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"{self.__class__.__name__}("
                f"id={self.task_id}, "
                f"inputs={[t.value for t in self.input_types]}, "
                f"outputs={[t.value for t in self.output_types]})")


class TaskConfig:
    """Configuration for task execution"""

    def __init__(self,
                 task_id: str,
                 inputs: Optional[Dict[str, Any]] = None,
                 settings: Optional[Dict[str, Any]] = None):
        """
        Initialize task configuration

        Args:
            task_id: Identifier of the task to execute
            inputs: Input mappings for the task
            settings: Task-specific settings
        """
        self.task_id = task_id
        self.inputs = inputs or {}
        self.settings = settings or {}
