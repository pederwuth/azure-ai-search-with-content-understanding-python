# Pipeline Architecture Documentation

## Overview

This implementation provides a complete task-based pipeline orchestration system for educational content processing. The architecture is designed to be modular, extensible, and maintainable while preserving backward compatibility with existing API endpoints.

## Architecture Components

### 1. Task System (`src/tasks/`)

#### Core Components
- **`base.py`**: Abstract base class `BaseTask` that all tasks must implement
- **`models.py`**: Data models for task inputs, outputs, metadata, and configurations
- **`registry.py`**: Central task registry with automatic discovery and validation
- **`executor.py`**: Pipeline executor with dependency resolution and orchestration

#### Task Implementations (`src/tasks/implementations/`)
- **`document_processing.py`**: Wraps enhanced document processor for PDF analysis
- **`summarization.py`**: Wraps summarization service for book summary generation
- **`flashcard_generation.py`**: Future task for generating flashcards (placeholder)
- **`quiz_generation.py`**: Future task for generating quizzes (placeholder)
- **`learning_objectives.py`**: Future task for extracting learning objectives (placeholder)

### 2. Pipeline System (`src/pipelines/`)

#### Core Components
- **`api.py`**: FastAPI router with pipeline management endpoints
- **`templates.py`**: Pre-built pipeline configurations for common workflows
- **`storage.py`**: Pipeline result persistence and retrieval system

#### Pipeline Templates
- **`document_to_summary`**: PDF → Enhanced Markdown → Summary
- **`complete_book_processing`**: Full educational workflow (extensible)
- **`document_processing_only`**: PDF processing without summarization
- **`summarization_only`**: Summary generation from existing markdown

### 3. API Integration (`src/api_server.py`)

The main API server integrates the pipeline router alongside existing endpoints, maintaining full backward compatibility.

## Available Endpoints

### Existing Endpoints (Preserved)
- `POST /enhanced/process` - Enhanced document processing
- `POST /summarization/upload` - Book summarization

### New Pipeline Endpoints
- `GET /pipeline/templates` - List available pipeline templates
- `GET /pipeline/templates/{template_id}` - Get specific template details
- `POST /pipeline/execute` - Execute a pipeline with custom configuration
- `GET /pipeline/jobs/{job_id}` - Get pipeline execution status and results

## Usage Examples

### 1. Execute Document to Summary Pipeline

```bash
curl -X POST "http://localhost:8000/pipeline/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "document_to_summary",
    "inputs": {
      "file_path": "data/sample_layout.pdf",
      "book_title": "Sample Book"
    },
    "settings": {
      "save_intermediates": true
    }
  }'
```

### 2. List Available Templates

```bash
curl -X GET "http://localhost:8000/pipeline/templates"
```

### 3. Execute Custom Pipeline Configuration

```bash
curl -X POST "http://localhost:8000/pipeline/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "Custom Processing",
      "description": "Custom document processing workflow",
      "tasks": [
        {
          "task_id": "document_processing",
          "inputs": {},
          "settings": {
            "analyzer_template": "analyzer_templates/content_document.json"
          }
        }
      ]
    },
    "inputs": {
      "file_path": "data/sample_report.pdf"
    }
  }'
```

## Task Development Guide

### Creating a New Task

1. **Implement the Task Class**:
```python
from ..base import BaseTask
from ..models import TaskInputs, TaskOutputs, TaskMetadata

class MyNewTask(BaseTask):
    @property
    def metadata(self) -> TaskMetadata:
        return TaskMetadata(
            task_id="my_new_task",
            name="My New Task",
            description="Description of what this task does",
            version="1.0.0",
            input_types=[TaskInputType.BOOK_SUMMARY],
            output_types=[TaskOutputType.METADATA],
            dependencies=["summarization"],
            estimated_duration_minutes=5
        )
    
    async def execute(self, inputs: TaskInputs) -> TaskOutputs:
        # Implementation here
        pass
```

2. **Register the Task**:
Add to `src/tasks/registry.py` in the `_register_builtin_tasks()` method:
```python
from .implementations.my_new_task import MyNewTask
# ... in _register_builtin_tasks():
self.register_task(MyNewTask())
```

3. **Add to Pipeline Templates**:
Update pipeline templates in `src/pipelines/templates.py` to include your new task.

### Task Input/Output Types

- **Input Types**: `PDF_FILE`, `ENHANCED_MARKDOWN`, `BOOK_SUMMARY`
- **Output Types**: `ENHANCED_MARKDOWN`, `BOOK_SUMMARY`, `FLASHCARDS`, `QUIZ`, `LEARNING_OBJECTIVES`, `METADATA`

## Extension Points

### 1. Future Educational Tasks

The system is ready for adding:
- **Flashcard Generation**: Create study flashcards from book content
- **Quiz Generation**: Generate assessments and tests
- **Learning Objectives**: Extract educational goals and outcomes
- **Study Guides**: Create comprehensive study materials
- **Concept Maps**: Generate visual learning aids

### 2. New Content Types

The task system can be extended for:
- **Video Content**: Processing and analysis of educational videos
- **Audio Content**: Transcription and analysis of lectures/audiobooks
- **Interactive Content**: Processing of interactive educational materials

### 3. Advanced Features

Future enhancements could include:
- **Conditional Execution**: Tasks that run based on content analysis
- **Parallel Execution**: Independent tasks running simultaneously
- **Result Caching**: Intelligent caching of task outputs
- **Progress Tracking**: Real-time pipeline execution monitoring

## System Benefits

### 1. Modularity
- Each task is self-contained and independently testable
- Easy to add, remove, or modify individual tasks
- Clear separation of concerns

### 2. Extensibility
- Simple framework for adding new educational processing tasks
- Template system for common workflow patterns
- Flexible configuration system

### 3. Maintainability
- Centralized task registry and dependency management
- Consistent error handling and logging
- Clear data flow and interface contracts

### 4. Backward Compatibility
- All existing API endpoints preserved
- Existing clients continue to work unchanged
- Gradual migration path to pipeline-based workflows

## Testing

### Unit Tests
Each task should have comprehensive unit tests covering:
- Task metadata validation
- Input/output processing
- Error handling
- Dependency requirements

### Integration Tests
Pipeline-level tests should cover:
- End-to-end workflow execution
- Template instantiation
- Dependency resolution
- Error propagation

### Example Test Structure
```python
import pytest
from src.tasks.implementations.my_task import MyTask
from src.tasks.models import TaskInputs

@pytest.mark.asyncio
async def test_my_task_execution():
    task = MyTask()
    inputs = TaskInputs()
    inputs.add_data('test_input', 'test_value')
    
    result = await task.execute(inputs)
    
    assert result.data['expected_output'] == 'expected_value'
```

## Deployment Considerations

### Resource Requirements
- Tasks specify their resource requirements (memory, Azure OpenAI access)
- Pipeline executor can validate resource availability before execution
- Background execution prevents blocking of API responses

### Scalability
- Tasks are designed to be stateless for horizontal scaling
- Pipeline storage supports distributed execution
- Job tracking enables async processing monitoring

### Monitoring
- Comprehensive logging at task and pipeline levels
- Execution metrics and performance tracking
- Error reporting and debugging information

This pipeline architecture provides a solid foundation for building sophisticated educational content processing workflows while maintaining simplicity and extensibility.