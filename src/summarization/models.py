"""
Data models for educational content summarization.

Contains dataclasses and models used throughout the summarization process.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from pathlib import Path
import json


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
    connections_to_previous: str = ""
    new_insights: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "summary": self.summary,
            "key_concepts": self.key_concepts,
            "main_topics": self.main_topics,
            "token_count": self.token_count,
            "connections_to_previous": self.connections_to_previous,
            "new_insights": self.new_insights,
            "created_at": self.created_at.isoformat()
        }


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
    book_structure: str = ""
    target_audience: str = ""
    practical_applications: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "book_title": self.book_title,
            "overall_summary": self.overall_summary,
            "key_themes": self.key_themes,
            "learning_objectives": self.learning_objectives,
            "book_structure": self.book_structure,
            "target_audience": self.target_audience,
            "practical_applications": self.practical_applications,
            "total_chapters": self.total_chapters,
            "created_at": self.created_at.isoformat(),
            "chapter_summaries": [cs.to_dict() for cs in self.chapter_summaries]
        }

    def save_to_file(self, filepath: Path) -> Path:
        """Save book summary to JSON file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath


@dataclass
class SummarizationResult:
    """Result of the summarization process"""
    book_summary: BookSummary
    output_directory: Path
    summary_file: Path
    metadata_file: Path
    processing_time_seconds: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "book_title": self.book_summary.book_title,
            "total_chapters": self.book_summary.total_chapters,
            "output_directory": str(self.output_directory),
            "summary_file": str(self.summary_file),
            "metadata_file": str(self.metadata_file),
            "processing_time_seconds": self.processing_time_seconds,
            "created_at": self.book_summary.created_at.isoformat()
        }