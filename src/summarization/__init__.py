"""
Educational Content Summarization Module

This module provides progressive summarization capabilities for educational content,
including markdown documents and processed content from the document understanding pipeline.

Components:
- models: Data models for chapters, summaries, and results
- prompts: LangChain prompt templates for educational summarization
- book_summarizer: Core progressive summarization logic
- router: FastAPI endpoints for summarization services
"""

from .models import (
    BookChapter,
    ChapterSummary,
    BookSummary,
    SummarizationResult
)

from .book_summarizer import ProgressiveBookSummarizer
from .router import router

__all__ = [
    "BookChapter",
    "ChapterSummary", 
    "BookSummary",
    "SummarizationResult",
    "ProgressiveBookSummarizer",
    "router"
]

__version__ = "1.0.0"
