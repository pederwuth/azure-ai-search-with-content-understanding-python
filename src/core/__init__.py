"""
Core module for educational content processing system.

This module contains the fundamental data structures and utilities
used throughout the educational content understanding and summarization pipeline.
"""

from .models import BookChapter, ChapterSummary, BookSummary
from .config import Settings
from .exceptions import (
    ContentUnderstandingError,
    SummarizationError,
    ProcessingError
)

__all__ = [
    "BookChapter",
    "ChapterSummary", 
    "BookSummary",
    "Settings",
    "ContentUnderstandingError",
    "SummarizationError",
    "ProcessingError"
]
