"""
JSON serialization utilities for educational content processing.

This module provides utilities for converting between Python objects
and JSON format, with proper error handling and validation.
"""

import json
from typing import Any, Dict
from pathlib import Path
import logging

from ..core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class JsonSerializer:
    """Handles JSON serialization and deserialization operations."""
    
    @staticmethod
    def save_to_file(data: Any, filepath: str, indent: int = 2) -> None:
        """Save data to JSON file.
        
        Args:
            data: Data to serialize (must be JSON serializable)
            filepath: Path where to save the file
            indent: JSON indentation level
            
        Raises:
            ProcessingError: If serialization or file writing fails
        """
        try:
            file_path = Path(filepath)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            logger.debug(f"JSON data saved to: {filepath}")
            
        except (TypeError, ValueError) as e:
            raise ProcessingError(f"JSON serialization failed: {e}") from e
        except OSError as e:
            raise ProcessingError(f"File write failed: {e}") from e
    
    @staticmethod
    def load_from_file(filepath: str) -> Any:
        """Load data from JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Deserialized data
            
        Raises:
            ProcessingError: If file reading or deserialization fails
        """
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                raise ProcessingError(f"JSON file not found: {filepath}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"JSON data loaded from: {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            raise ProcessingError(f"JSON parsing failed: {e}") from e
        except OSError as e:
            raise ProcessingError(f"File read failed: {e}") from e
    
    @staticmethod
    def to_json_string(data: Any, indent: int = 2) -> str:
        """Convert data to JSON string.
        
        Args:
            data: Data to serialize
            indent: JSON indentation level
            
        Returns:
            JSON string representation
            
        Raises:
            ProcessingError: If serialization fails
        """
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ProcessingError(f"JSON serialization failed: {e}") from e
    
    @staticmethod
    def from_json_string(json_str: str) -> Any:
        """Parse data from JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Parsed data
            
        Raises:
            ProcessingError: If parsing fails
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ProcessingError(f"JSON parsing failed: {e}") from e
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_fields: list) -> bool:
        """Validate that JSON data contains required fields.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present
            
        Raises:
            ProcessingError: If validation fails
        """
        if not isinstance(data, dict):
            raise ProcessingError("Data must be a dictionary")
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ProcessingError(f"Missing required fields: {missing_fields}")
        
        return True
    
    @staticmethod
    def pretty_print(data: Any) -> str:
        """Create a pretty-printed JSON string for debugging.
        
        Args:
            data: Data to format
            
        Returns:
            Pretty-formatted JSON string
        """
        try:
            return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            return str(data)  # Fallback to string representation
