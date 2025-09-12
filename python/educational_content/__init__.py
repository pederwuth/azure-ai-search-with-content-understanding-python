"""
Educational Content Generation Module

This module provides tools for generating educational content from documents
using Azure AI services and GPT-5 for enhanced learning experiences.
"""

from .chapter_chunker import ChapterChunker
from .summary_generator import SummaryGenerator
from .file_manager import EducationalFileManager

__all__ = ['ChapterChunker', 'SummaryGenerator', 'EducationalFileManager']
