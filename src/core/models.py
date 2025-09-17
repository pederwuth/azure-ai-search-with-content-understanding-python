"""
Data models for educational content processing.

This module contains the core data structures used throughout
the educational content understanding and summarization pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class BookChapter:
    """Represents a chapter from a document.

    Attributes:
        chapter_number: Sequential number of the chapter
        title: Chapter title or heading
        content: Full text content of the chapter
        token_count: Number of tokens in the chapter content
        page_range: Page range information (e.g., "Pages 1-5")
    """
    chapter_number: int
    title: str
    content: str
    token_count: int
    page_range: str

    def __post_init__(self):
        """Validate chapter data after initialization."""
        if not self.title.strip():
            self.title = f"Chapter {self.chapter_number}"
        if self.token_count < 0:
            raise ValueError("Token count cannot be negative")


@dataclass
class ChapterSummary:
    """Represents a generated chapter summary.

    Attributes:
        chapter_number: Sequential number of the chapter
        chapter_title: Title of the chapter
        summary: Generated summary text
        key_concepts: List of main concepts identified
        main_topics: List of primary topics covered
        token_count: Number of tokens in the summary
        created_at: Timestamp when summary was generated
    """
    chapter_number: int
    chapter_title: str
    summary: str
    key_concepts: List[str]
    main_topics: List[str]
    token_count: int
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "summary": self.summary,
            "key_concepts": self.key_concepts,
            "main_topics": self.main_topics,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChapterSummary':
        """Create from dictionary (e.g., from JSON)."""
        return cls(
            chapter_number=data["chapter_number"],
            chapter_title=data["chapter_title"],
            summary=data["summary"],
            key_concepts=data["key_concepts"],
            main_topics=data["main_topics"],
            token_count=data["token_count"],
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class BookSummary:
    """Represents the final comprehensive book summary.

    Attributes:
        book_title: Title of the book
        overall_summary: Comprehensive book summary
        chapter_summaries: List of individual chapter summaries
        key_themes: Major themes identified across the book
        learning_objectives: Educational objectives from the content
        total_chapters: Total number of chapters
        created_at: Timestamp when book summary was generated
    """
    book_title: str
    overall_summary: str
    chapter_summaries: List[ChapterSummary]
    key_themes: List[str]
    learning_objectives: List[str]
    total_chapters: int
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "book_title": self.book_title,
            "overall_summary": self.overall_summary,
            "key_themes": self.key_themes,
            "learning_objectives": self.learning_objectives,
            "total_chapters": self.total_chapters,
            "created_at": self.created_at.isoformat(),
            "chapter_summaries": [cs.to_dict() for cs in self.chapter_summaries]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BookSummary':
        """Create from dictionary (e.g., from JSON)."""
        return cls(
            book_title=data["book_title"],
            overall_summary=data["overall_summary"],
            key_themes=data["key_themes"],
            learning_objectives=data["learning_objectives"],
            total_chapters=data["total_chapters"],
            created_at=datetime.fromisoformat(data["created_at"]),
            chapter_summaries=[
                ChapterSummary.from_dict(cs) for cs in data["chapter_summaries"]
            ]
        )

    def save_to_json(self, filepath: str) -> None:
        """Save book summary to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_json(cls, filepath: str) -> 'BookSummary':
        """Load book summary from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_summary_stats(self) -> dict:
        """Get summary statistics about the book."""
        total_summary_tokens = sum(
            cs.token_count for cs in self.chapter_summaries)
        avg_chapter_tokens = total_summary_tokens / \
            len(self.chapter_summaries) if self.chapter_summaries else 0

        return {
            "total_chapters": self.total_chapters,
            "total_summary_tokens": total_summary_tokens,
            "average_chapter_tokens": round(avg_chapter_tokens, 1),
            "key_themes_count": len(self.key_themes),
            "learning_objectives_count": len(self.learning_objectives),
            "created_at": self.created_at.isoformat()
        }
