"""
Pipeline Storage

Handles storage and retrieval of pipeline execution results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..tasks.models import PipelineResult, TaskStatus

logger = logging.getLogger(__name__)


class PipelineStorage:
    """Handles storage and retrieval of pipeline results"""

    def __init__(self, base_dir: str = "content/pipelines"):
        """
        Initialize pipeline storage

        Args:
            base_dir: Base directory for pipeline storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def save_pipeline_result(self, result: PipelineResult) -> Path:
        """
        Save pipeline result to storage

        Args:
            result: Pipeline execution result to save

        Returns:
            Path: Path where result was saved
        """
        pipeline_dir = self.base_dir / f"pipeline_{result.pipeline_id}"
        pipeline_dir.mkdir(parents=True, exist_ok=True)

        # Save detailed result
        result_file = pipeline_dir / "result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self._serialize_result(result),
                      f, indent=2, ensure_ascii=False)

        # Save summary for quick listing
        self._update_pipeline_index(result)

        self.logger.info(f"Saved pipeline result: {result.pipeline_id}")
        return pipeline_dir

    def load_pipeline_result(self, pipeline_id: str) -> Optional[PipelineResult]:
        """
        Load pipeline result from storage

        Args:
            pipeline_id: ID of the pipeline to load

        Returns:
            PipelineResult: Loaded pipeline result or None if not found
        """
        result_file = self.base_dir / f"pipeline_{pipeline_id}" / "result.json"

        if not result_file.exists():
            return None

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._deserialize_result(data)

        except Exception as e:
            self.logger.error(
                f"Failed to load pipeline result {pipeline_id}: {e}")
            return None

    def list_pipelines(self,
                       status: Optional[TaskStatus] = None,
                       limit: Optional[int] = None) -> List[Dict[str, any]]:
        """
        List pipeline executions

        Args:
            status: Filter by status (optional)
            limit: Maximum number of results (optional)

        Returns:
            List[Dict]: List of pipeline summaries
        """
        index_file = self.base_dir / "pipeline_index.json"

        if not index_file.exists():
            return []

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                pipelines = json.load(f)

            # Filter by status if specified
            if status:
                pipelines = [p for p in pipelines if p.get(
                    'status') == status.value]

            # Sort by start time (most recent first)
            pipelines.sort(key=lambda x: x.get('start_time', ''), reverse=True)

            # Apply limit if specified
            if limit:
                pipelines = pipelines[:limit]

            return pipelines

        except Exception as e:
            self.logger.error(f"Failed to list pipelines: {e}")
            return []

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """
        Delete a pipeline and its results

        Args:
            pipeline_id: ID of the pipeline to delete

        Returns:
            bool: True if deleted successfully
        """
        pipeline_dir = self.base_dir / f"pipeline_{pipeline_id}"

        if not pipeline_dir.exists():
            return False

        try:
            import shutil
            shutil.rmtree(pipeline_dir)

            # Remove from index
            self._remove_from_index(pipeline_id)

            self.logger.info(f"Deleted pipeline: {pipeline_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete pipeline {pipeline_id}: {e}")
            return False

    def _serialize_result(self, result: PipelineResult) -> Dict[str, any]:
        """Serialize pipeline result to JSON-compatible format"""
        return {
            "pipeline_id": result.pipeline_id,
            "config": {
                "name": result.config.name,
                "description": result.config.description,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "inputs": task.inputs,
                        "settings": task.settings
                    } for task in result.config.tasks
                ],
                "settings": result.config.settings,
                "metadata": result.config.metadata
            },
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "error_message": result.error_message,
            "task_executions": {
                task_id: {
                    "task_id": execution.task_id,
                    "status": execution.status.value,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "error_message": execution.error_message,
                    "execution_metadata": execution.execution_metadata
                } for task_id, execution in result.task_executions.items()
            },
            "final_outputs": {
                "data": result.final_outputs.data if result.final_outputs else {},
                "files": {k: str(v) for k, v in result.final_outputs.files.items()} if result.final_outputs else {},
                "metadata": result.final_outputs.metadata if result.final_outputs else {}
            } if result.final_outputs else None
        }

    def _deserialize_result(self, data: Dict[str, any]) -> PipelineResult:
        """Deserialize pipeline result from JSON format"""
        # This is a simplified deserialization for basic use cases
        # Full deserialization would require recreating all objects
        from ..tasks.models import PipelineConfig, TaskConfig, TaskExecution, TaskOutputs

        # Recreate config
        config = PipelineConfig(
            name=data["config"]["name"],
            description=data["config"]["description"],
            tasks=[
                TaskConfig(
                    task_id=task["task_id"],
                    inputs=task["inputs"],
                    settings=task["settings"]
                ) for task in data["config"]["tasks"]
            ],
            settings=data["config"]["settings"],
            metadata=data["config"]["metadata"]
        )

        # Recreate result
        result = PipelineResult(
            pipeline_id=data["pipeline_id"],
            config=config,
            status=TaskStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(
                data["end_time"]) if data["end_time"] else None,
            error_message=data.get("error_message")
        )

        # Add task executions (simplified)
        for task_id, exec_data in data.get("task_executions", {}).items():
            execution = TaskExecution(
                task_id=exec_data["task_id"],
                status=TaskStatus(exec_data["status"]),
                start_time=datetime.fromisoformat(
                    exec_data["start_time"]) if exec_data["start_time"] else None,
                end_time=datetime.fromisoformat(
                    exec_data["end_time"]) if exec_data["end_time"] else None,
                error_message=exec_data.get("error_message"),
                execution_metadata=exec_data.get("execution_metadata", {})
            )
            result.task_executions[task_id] = execution

        return result

    def _update_pipeline_index(self, result: PipelineResult) -> None:
        """Update the pipeline index with new result"""
        index_file = self.base_dir / "pipeline_index.json"

        # Load existing index
        pipelines = []
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    pipelines = json.load(f)
            except Exception:
                pipelines = []

        # Remove existing entry for this pipeline
        pipelines = [p for p in pipelines if p.get(
            'pipeline_id') != result.pipeline_id]

        # Add new entry
        pipeline_summary = {
            "pipeline_id": result.pipeline_id,
            "name": result.config.name,
            "description": result.config.description,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "task_count": len(result.config.tasks),
            "error_message": result.error_message
        }
        pipelines.append(pipeline_summary)

        # Save updated index
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(pipelines, f, indent=2, ensure_ascii=False)

    def _remove_from_index(self, pipeline_id: str) -> None:
        """Remove pipeline from index"""
        index_file = self.base_dir / "pipeline_index.json"

        if not index_file.exists():
            return

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                pipelines = json.load(f)

            # Remove the pipeline
            pipelines = [p for p in pipelines if p.get(
                'pipeline_id') != pipeline_id]

            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(pipelines, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to remove pipeline from index: {e}")
