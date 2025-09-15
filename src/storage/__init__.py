"""
Storage module for educational content processing.

This module handles file I/O operations, JSON serialization,
and output management for the educational content pipeline.
"""

from .file_manager import FileManager
from .json_serializer import JsonSerializer

__all__ = ["FileManager", "JsonSerializer"]
