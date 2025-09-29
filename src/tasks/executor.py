"""
Pipeline Executor

Executes task pipelines with dependency resolution and error handling.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseTask
from .models import (
    TaskInputs, TaskOutputs, TaskExecution, PipelineResult,
    PipelineConfig, TaskStatus, TaskConfig
)
from .registry import get_task_registry

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Executes task pipelines with dependency resolution"""

    def __init__(self, output_base_dir: str = "content/pipelines"):
        """
        Initialize pipeline executor

        Args:
            output_base_dir: Base directory for pipeline outputs
        """
        self.registry = get_task_registry()
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def execute_pipeline(self,
                               config: PipelineConfig,
                               initial_inputs: Dict[str, Any],
                               pipeline_id: Optional[str] = None) -> PipelineResult:
        """
        Execute a complete pipeline

        Args:
            config: Pipeline configuration
            initial_inputs: Initial inputs for the pipeline
            pipeline_id: Optional pipeline ID (generated if not provided)

        Returns:
            PipelineResult: Result of pipeline execution
        """
        if pipeline_id is None:
            pipeline_id = str(uuid.uuid4())

        self.logger.info(f"Starting pipeline execution: {pipeline_id}")
        self.logger.info(f"Pipeline: {config.name}")

        # Create pipeline result
        result = PipelineResult(
            pipeline_id=pipeline_id,
            config=config,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )

        try:
            # Create output directory for this pipeline
            pipeline_output_dir = self.output_base_dir / \
                f"pipeline_{pipeline_id}"
            pipeline_output_dir.mkdir(parents=True, exist_ok=True)

            # Resolve task execution order
            task_ids = [task.task_id for task in config.tasks]
            execution_order = self.registry.resolve_dependencies(task_ids)

            self.logger.info(f"Execution order: {execution_order}")

            # Execute tasks in order
            available_outputs = TaskOutputs()

            # Add initial inputs to available outputs
            for key, value in initial_inputs.items():
                if isinstance(value, (str, Path)) and Path(value).exists():
                    available_outputs.add_file(key, value)
                else:
                    available_outputs.add_data(key, value)

            for task_id in execution_order:
                # Find task config
                task_config = None
                for t in config.tasks:
                    if t.task_id == task_id:
                        task_config = t
                        break

                if task_config is None:
                    # This is a dependency task, create minimal config
                    task_config = TaskConfig(task_id=task_id)

                # Execute task
                task_execution = await self._execute_task(
                    task_config,
                    available_outputs,
                    pipeline_output_dir
                )

                result.task_executions[task_id] = task_execution

                # Check if task failed
                if task_execution.status == TaskStatus.FAILED:
                    result.status = TaskStatus.FAILED
                    result.error_message = f"Task '{task_id}' failed: {task_execution.error_message}"
                    break

                # Add task outputs to available outputs
                if task_execution.outputs:
                    available_outputs.data.update(task_execution.outputs.data)
                    available_outputs.files.update(
                        task_execution.outputs.files)
                    available_outputs.metadata.update(
                        task_execution.outputs.metadata)

            # Set final results
            if result.status != TaskStatus.FAILED:
                result.status = TaskStatus.COMPLETED
                result.final_outputs = available_outputs

            result.end_time = datetime.now()

            # Save pipeline metadata
            await self._save_pipeline_metadata(result, pipeline_output_dir)

            self.logger.info(
                f"Pipeline execution completed: {pipeline_id} ({result.status})")
            if result.duration_seconds:
                self.logger.info(
                    f"Total duration: {result.duration_seconds:.2f} seconds")

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            result.status = TaskStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()

        return result

    async def _execute_task(self,
                            config: TaskConfig,
                            available_outputs: TaskOutputs,
                            output_dir: Path) -> TaskExecution:
        """
        Execute a single task

        Args:
            config: Task configuration
            available_outputs: Outputs from previous tasks
            output_dir: Directory for task outputs

        Returns:
            TaskExecution: Result of task execution
        """
        task_execution = TaskExecution(
            task_id=config.task_id,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )

        try:
            self.logger.info(f"Executing task: {config.task_id}")

            # Get task instance
            task = self.registry.get_task(config.task_id)

            # Prepare task inputs
            task_inputs = self._prepare_task_inputs(config, available_outputs)
            task_execution.inputs = task_inputs

            # Validate inputs
            if not task.validate_inputs(task_inputs):
                raise ValueError(f"Invalid inputs for task {config.task_id}")

            # Setup task
            await task.setup()

            try:
                # Execute task
                task_outputs = await task.execute(task_inputs)

                # Save task outputs to directory
                await self._save_task_outputs(config.task_id, task_outputs, output_dir)

                task_execution.outputs = task_outputs
                task_execution.status = TaskStatus.COMPLETED

                self.logger.info(f"Task completed: {config.task_id}")

            finally:
                # Cleanup task
                await task.cleanup()

        except Exception as e:
            self.logger.error(f"Task failed: {config.task_id} - {e}")
            task_execution.status = TaskStatus.FAILED
            task_execution.error_message = str(e)

        task_execution.end_time = datetime.now()
        return task_execution

    def _prepare_task_inputs(self,
                             config: TaskConfig,
                             available_outputs: TaskOutputs) -> TaskInputs:
        """
        Prepare inputs for a task based on config and available outputs

        Args:
            config: Task configuration
            available_outputs: Available outputs from previous tasks

        Returns:
            TaskInputs: Prepared inputs for the task
        """
        task_inputs = TaskInputs()

        # Add configured inputs
        for key, value in config.inputs.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to available output
                output_key = value[1:]  # Remove $ prefix
                if output_key in available_outputs.data:
                    task_inputs.add_data(
                        key, available_outputs.data[output_key])
                elif output_key in available_outputs.files:
                    task_inputs.files[key] = available_outputs.files[output_key]
            else:
                # Direct value
                task_inputs.add_data(key, value)

        # Add all available outputs that match task input types
        task_metadata = self.registry.get_task_metadata(config.task_id)
        for input_type in task_metadata.input_types:
            input_key = input_type.value
            if input_key in available_outputs.data:
                task_inputs.add_data(
                    input_key, available_outputs.data[input_key])
            if input_key in available_outputs.files:
                task_inputs.files[input_key] = available_outputs.files[input_key]

        # Also pass ALL available data to support custom parameters like custom_filename, original_filename, etc.
        for key, value in available_outputs.data.items():
            if key not in task_inputs.data:  # Don't overwrite already set inputs
                task_inputs.add_data(key, value)

        return task_inputs

    async def _save_task_outputs(self,
                                 task_id: str,
                                 outputs: TaskOutputs,
                                 base_dir: Path) -> None:
        """
        Save task outputs to directory

        Args:
            task_id: ID of the task
            outputs: Task outputs to save
            base_dir: Base directory for outputs
        """
        task_dir = base_dir / f"task_{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Update file paths to be within task directory
        for key, file_path in outputs.files.items():
            if file_path.exists():
                new_path = task_dir / file_path.name
                # Copy file if it's not already in the right location
                if file_path.resolve() != new_path.resolve():
                    import shutil
                    shutil.copy2(file_path, new_path)
                    outputs.files[key] = new_path

    async def _save_pipeline_metadata(self,
                                      result: PipelineResult,
                                      output_dir: Path) -> None:
        """
        Save pipeline execution metadata

        Args:
            result: Pipeline execution result
            output_dir: Output directory
        """
        import json

        metadata = {
            "pipeline_id": result.pipeline_id,
            "config": {
                "name": result.config.name,
                "description": result.config.description,
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "inputs": t.inputs,
                        "settings": t.settings
                    } for t in result.config.tasks
                ]
            },
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "duration_seconds": result.duration_seconds,
            "error_message": result.error_message,
            "task_executions": {
                task_id: {
                    "status": execution.status.value,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "duration_seconds": execution.duration_seconds,
                    "error_message": execution.error_message
                } for task_id, execution in result.task_executions.items()
            }
        }

        metadata_file = output_dir / "pipeline_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    async def execute_task_sequence(self,
                                    task_ids: List[str],
                                    inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tasks in sequence (simple version)

        Args:
            task_ids: List of task IDs to execute in order
            inputs: Initial inputs

        Returns:
            Dict[str, Any]: Final outputs
        """
        # Create simple pipeline config
        config = PipelineConfig(
            name="sequential_execution",
            description=f"Sequential execution of: {', '.join(task_ids)}",
            tasks=[TaskConfig(task_id=task_id) for task_id in task_ids]
        )

        result = await self.execute_pipeline(config, inputs)

        if result.status == TaskStatus.FAILED:
            raise RuntimeError(
                f"Pipeline execution failed: {result.error_message}")

        return result.final_outputs.data if result.final_outputs else {}
