"""
Book summarization module.

Provides progressive book summarization capabilities using Azure OpenAI.
"""

from .models import BookChapter, ChapterSummary, BookSummary
from .book_summarizer import ProgressiveBookSummarizer

__all__ = [
    'BookChapter',
    'ChapterSummary',
    'BookSummary',
    'ProgressiveBookSummarizer'
]
