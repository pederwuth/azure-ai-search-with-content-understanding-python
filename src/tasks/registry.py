"""
Task Registry

Central registry for all available tasks with discovery and dependency resolution.
"""

import logging
from typing import Dict, List, Type, Optional, Set
from collections import defaultdict, deque

from .base import BaseTask
from .models import TaskMetadata

logger = logging.getLogger(__name__)


class TaskRegistry:
    """Central registry for all available tasks"""
    
    def __init__(self):
        """Initialize the task registry"""
        self._tasks: Dict[str, Type[BaseTask]] = {}
        self._metadata: Dict[str, TaskMetadata] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_task(self, task_class: Type[BaseTask]) -> None:
        """
        Register a new task type
        
        Args:
            task_class: Task class to register
        """
        # Create a temporary instance to get metadata
        temp_instance = task_class()
        metadata = temp_instance.metadata
        
        if metadata.task_id in self._tasks:
            self.logger.warning(f"Task {metadata.task_id} is already registered, overwriting")
        
        self._tasks[metadata.task_id] = task_class
        self._metadata[metadata.task_id] = metadata
        
        self.logger.info(f"Registered task: {metadata.task_id}")
    
    def get_task(self, task_id: str) -> BaseTask:
        """
        Get task instance by ID
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            BaseTask: Instance of the requested task
            
        Raises:
            ValueError: If task is not registered
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task '{task_id}' is not registered. Available tasks: {list(self._tasks.keys())}")
        
        return self._tasks[task_id]()
    
    def get_task_metadata(self, task_id: str) -> TaskMetadata:
        """
        Get metadata for a task
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskMetadata: Metadata for the task
        """
        if task_id not in self._metadata:
            raise ValueError(f"Task '{task_id}' is not registered")
        
        return self._metadata[task_id]
    
    def list_tasks(self) -> List[str]:
        """
        List all registered task IDs
        
        Returns:
            List[str]: List of task IDs
        """
        return list(self._tasks.keys())
    
    def list_task_metadata(self) -> List[TaskMetadata]:
        """
        List metadata for all registered tasks
        
        Returns:
            List[TaskMetadata]: List of task metadata
        """
        return list(self._metadata.values())
    
    def find_compatible_tasks(self, available_outputs: Dict[str, any]) -> List[str]:
        """
        Find tasks that can run with current outputs
        
        Args:
            available_outputs: Outputs available from previous tasks
            
        Returns:
            List[str]: List of task IDs that can process the available outputs
        """
        compatible_tasks = []
        
        for task_id in self._tasks:
            task_instance = self.get_task(task_id)
            if task_instance.can_process(available_outputs):
                compatible_tasks.append(task_id)
        
        return compatible_tasks
    
    def resolve_dependencies(self, target_tasks: List[str]) -> List[str]:
        """
        Resolve task dependencies and return execution order
        
        Args:
            target_tasks: List of task IDs to execute
            
        Returns:
            List[str]: Task IDs in dependency-resolved execution order
            
        Raises:
            ValueError: If circular dependencies are detected or dependencies are missing
        """
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        all_tasks = set(target_tasks)
        
        # Add dependencies to the set of tasks to process
        def add_dependencies(task_id: str):
            if task_id not in self._metadata:
                raise ValueError(f"Task '{task_id}' is not registered")
            
            metadata = self._metadata[task_id]
            for dep in metadata.dependencies:
                if dep not in all_tasks:
                    all_tasks.add(dep)
                    add_dependencies(dep)
                graph[dep].append(task_id)
                in_degree[task_id] += 1
        
        # Build complete dependency graph
        for task_id in target_tasks:
            add_dependencies(task_id)
        
        # Initialize in-degree for all tasks
        for task_id in all_tasks:
            if task_id not in in_degree:
                in_degree[task_id] = 0
        
        # Topological sort using Kahn's algorithm
        queue = deque([task_id for task_id in all_tasks if in_degree[task_id] == 0])
        execution_order = []
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            
            # Reduce in-degree for dependent tasks
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for circular dependencies
        if len(execution_order) != len(all_tasks):
            remaining = all_tasks - set(execution_order)
            raise ValueError(f"Circular dependency detected involving tasks: {remaining}")
        
        # Filter to only return tasks that were originally requested or their dependencies
        return execution_order
    
    def get_task_info(self, task_id: str) -> Dict[str, any]:
        """
        Get comprehensive information about a task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dict: Comprehensive task information
        """
        metadata = self.get_task_metadata(task_id)
        
        return {
            "task_id": metadata.task_id,
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "input_types": [t.value for t in metadata.input_types],
            "output_types": [t.value for t in metadata.output_types],
            "dependencies": metadata.dependencies,
            "estimated_duration_minutes": metadata.estimated_duration_minutes,
            "resource_requirements": metadata.resource_requirements
        }
    
    def validate_task_chain(self, task_ids: List[str]) -> Dict[str, any]:
        """
        Validate that a chain of tasks can be executed
        
        Args:
            task_ids: List of task IDs to validate
            
        Returns:
            Dict: Validation result with success status and any issues
        """
        issues = []
        
        try:
            # Check if all tasks are registered
            for task_id in task_ids:
                if task_id not in self._tasks:
                    issues.append(f"Task '{task_id}' is not registered")
            
            # Check dependency resolution
            if not issues:
                resolved_order = self.resolve_dependencies(task_ids)
                # Verify input/output compatibility in the chain
                available_outputs = set()
                
                for task_id in resolved_order:
                    metadata = self._metadata[task_id]
                    
                    # Check if task has required inputs available
                    required_inputs = set(t.value for t in metadata.input_types)
                    if required_inputs and not (required_inputs & available_outputs):
                        # First task or tasks that don't need previous outputs are OK
                        if task_id not in task_ids or available_outputs:
                            issues.append(f"Task '{task_id}' requires inputs {required_inputs} but only {available_outputs} are available")
                    
                    # Add this task's outputs to available outputs
                    available_outputs.update(t.value for t in metadata.output_types)
            
        except Exception as e:
            issues.append(str(e))
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "execution_order": resolved_order if not issues else None
        }


# Global registry instance
_registry: Optional[TaskRegistry] = None


def get_task_registry() -> TaskRegistry:
    """Get the global task registry instance"""
    global _registry
    if _registry is None:
        _registry = TaskRegistry()
        # Auto-register built-in tasks
        _register_builtin_tasks()
    return _registry


def _register_builtin_tasks():
    """Register built-in tasks"""
    registry = _registry
    
    try:
        # Import and register document processing task
        from .implementations.document_processing import DocumentProcessingTask
        registry.register_task(DocumentProcessingTask)
    except ImportError as e:
        logger.warning(f"Could not register DocumentProcessingTask: {e}")
    
    try:
        # Import and register summarization task
        from .implementations.summarization import SummarizationTask
        registry.register_task(SummarizationTask)
    except ImportError as e:
        logger.warning(f"Could not register SummarizationTask: {e}")
    
    # Future tasks will be added here automatically
    logger.info(f"Registered {len(registry.list_tasks())} built-in tasks")