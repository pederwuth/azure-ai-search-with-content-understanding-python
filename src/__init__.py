"""
Educational Content Processing System

A comprehensive Python package for processing educational documents using Azure AI services.
This system provides document understanding, content extraction, and progressive book summarization.

Main Components:
- Content Understanding: PDF processing with Azure Document Intelligence and Content Understanding
- Progressive Summarization: Chapter-by-chapter analysis with cumulative context building
- Storage Management: Organized file handling and JSON serialization
- Pipeline Orchestration: End-to-end workflow management

Example Usage:
    from src.pipeline.orchestrator import EducationalContentPipeline
    
    pipeline = EducationalContentPipeline()
    book_summary = pipeline.process_document_complete("document.pdf")
"""

__version__ = "1.0.0"
__author__ = "Educational Content Processing Team"

# Core exports
from .core import (
    BookChapter,
    ChapterSummary,
    BookSummary,
    Settings,
    ProcessingError,
    ContentUnderstandingError,
    SummarizationError
)

__all__ = [
    "BookChapter",
    "ChapterSummary",
    "BookSummary",
    "Settings",
    "ProcessingError",
    "ContentUnderstandingError",
    "SummarizationError"
]
