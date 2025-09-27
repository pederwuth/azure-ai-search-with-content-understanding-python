"""
Data models for book summarization pipeline.
Matches the exact structure from book_summary_generator.ipynb
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class BookChapter:
    """Represents a chapter from the document"""
    chapter_number: int
    title: str
    content: str
    token_count: int
    page_range: str


@dataclass
class ChapterSummary:
    """Represents a generated chapter summary"""
    chapter_number: int
    chapter_title: str
    summary: str
    key_concepts: List[str]
    main_topics: List[str]
    token_count: int
    created_at: datetime


@dataclass
class BookSummary:
    """Represents the final comprehensive book summary"""
    book_title: str
    overall_summary: str
    chapter_summaries: List[ChapterSummary]
    key_themes: List[str]
    learning_objectives: List[str]
    total_chapters: int
    created_at: datetime
