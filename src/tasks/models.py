"""
Task Models

Data models for the task system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Status of a task execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskInputType(str, Enum):
    """Types of inputs that tasks can accept"""
    PDF = "pdf"
    MARKDOWN = "markdown"
    ENHANCED_MARKDOWN = "enhanced_markdown"
    BOOK_SUMMARY = "book_summary"
    FIGURES = "figures"
    CACHE_FILE = "cache_file"
    METADATA = "metadata"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    LEARNING_OBJECTIVES = "learning_objectives"


class TaskOutputType(str, Enum):
    """Enumeration of task output types"""
    ENHANCED_MARKDOWN = "enhanced_markdown"
    BOOK_SUMMARY = "book_summary"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"
    LEARNING_OBJECTIVES = "learning_objectives"
    FIGURES = "figures"
    CACHE_FILE = "cache_file"
    METADATA = "metadata"


@dataclass
class TaskInputs:
    """Input data for a task"""
    data: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, Path] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_file(self, key: str) -> Optional[Path]:
        """Get a file path by key"""
        return self.files.get(key)

    def get_data(self, key: str) -> Any:
        """Get data by key"""
        return self.data.get(key)

    def has_file(self, key: str) -> bool:
        """Check if file exists"""
        return key in self.files and self.files[key].exists()

    def add_data(self, key: str, value: Any):
        """Add data to inputs"""
        self.data[key] = value

    def add_file(self, key: str, file_path: Union[str, Path]):
        """Add a file to inputs"""
        self.files[key] = Path(file_path)


@dataclass
class TaskOutputs:
    """Output data from a task"""
    data: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, Path] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, key: str, file_path: Union[str, Path]):
        """Add a file to outputs"""
        self.files[key] = Path(file_path)

    def add_data(self, key: str, value: Any):
        """Add data to outputs"""
        self.data[key] = value


@dataclass
class TaskConfig:
    """Configuration for a task"""
    task_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TaskMetadata:
    """Metadata about a task"""
    task_id: str
    name: str
    description: str
    version: str
    input_types: List[TaskInputType]
    output_types: List[TaskOutputType]
    dependencies: List[str] = field(default_factory=list)
    estimated_duration_minutes: Optional[int] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """Information about a task execution"""
    task_id: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    inputs: Optional[TaskInputs] = None
    outputs: Optional[TaskOutputs] = None
    error_message: Optional[str] = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class PipelineConfig(BaseModel):
    """Configuration for a pipeline"""
    name: str
    description: str
    tasks: List[TaskConfig]
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


@dataclass
class PipelineResult:
    """Result of a pipeline execution"""
    pipeline_id: str
    config: PipelineConfig
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    task_executions: Dict[str, TaskExecution] = field(default_factory=dict)
    final_outputs: Optional[TaskOutputs] = None
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate pipeline duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def get_task_execution(self, task_id: str) -> Optional[TaskExecution]:
        """Get execution info for a specific task"""
        return self.task_executions.get(task_id)
