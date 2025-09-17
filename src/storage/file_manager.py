"""
File management utilities for educational content processing.

This module provides centralized file handling for the educational content
pipeline, including path management, directory creation, and file operations.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging

from ..core.models import BookSummary
from ..core.exceptions import FileNotFoundError, ProcessingError

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for educational content processing."""

    def __init__(self, base_output_dir: str = "educational_content"):
        """Initialize file manager with base output directory.

        Args:
            base_output_dir: Base directory for all output files
        """
        self.base_dir = Path(base_output_dir)
        self.summaries_dir = self.base_dir / "book_summaries"
        self.markdown_dir = self.base_dir
        self.figures_dir = self.base_dir / "figures"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directories if they don't exist."""
        for directory in [self.base_dir, self.summaries_dir, self.figures_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def save_book_summary(
        self,
        book_summary: BookSummary,
        custom_filename: Optional[str] = None
    ) -> Path:
        """Save book summary to JSON file.

        Args:
            book_summary: BookSummary instance to save
            custom_filename: Optional custom filename (with .json extension)

        Returns:
            Path to the saved file

        Raises:
            ProcessingError: If save operation fails
        """
        try:
            if custom_filename:
                filename = custom_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = self._sanitize_filename(book_summary.book_title)
                filename = f"{safe_title}_summary_{timestamp}.json"

            filepath = self.summaries_dir / filename
            book_summary.save_to_json(str(filepath))

            logger.info(f"Book summary saved to: {filepath}")
            return filepath

        except Exception as e:
            raise ProcessingError(f"Failed to save book summary: {e}") from e

    def load_book_summary(self, filepath: str) -> BookSummary:
        """Load book summary from JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            BookSummary instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ProcessingError: If loading fails
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Book summary file not found: {filepath}")

        try:
            return BookSummary.load_from_json(str(file_path))
        except Exception as e:
            raise ProcessingError(f"Failed to load book summary: {e}") from e

    def save_markdown_content(
        self,
        content: str,
        title: str,
        custom_filename: Optional[str] = None
    ) -> Path:
        """Save markdown content to file.

        Args:
            content: Markdown content to save
            title: Title for the document (used in filename if no custom name)
            custom_filename: Optional custom filename

        Returns:
            Path to the saved file
        """
        try:
            if custom_filename:
                filename = custom_filename
            else:
                safe_title = self._sanitize_filename(title)
                filename = f"{safe_title}_markdown.md"

            filepath = self.markdown_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Markdown content saved to: {filepath}")
            return filepath

        except Exception as e:
            raise ProcessingError(
                f"Failed to save markdown content: {e}") from e

    def load_markdown_content(self, filepath: str) -> str:
        """Load markdown content from file.

        Args:
            filepath: Path to the markdown file

        Returns:
            Markdown content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            ProcessingError: If loading fails
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {filepath}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ProcessingError(
                f"Failed to load markdown content: {e}") from e

    def list_book_summaries(self) -> List[Path]:
        """List all book summary files.

        Returns:
            List of paths to book summary JSON files
        """
        return list(self.summaries_dir.glob("*.json"))

    def list_markdown_files(self) -> List[Path]:
        """List all markdown files.

        Returns:
            List of paths to markdown files
        """
        return list(self.markdown_dir.glob("*.md"))

    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up files older than specified days.

        Args:
            days_old: Files older than this many days will be deleted

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        deleted_count = 0

        for directory in [self.summaries_dir, self.figures_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

        return deleted_count

    def get_storage_stats(self) -> dict:
        """Get storage statistics.

        Returns:
            Dictionary with storage information
        """
        def get_dir_size(directory: Path) -> int:
            return sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())

        return {
            "base_directory": str(self.base_dir),
            "total_size_bytes": get_dir_size(self.base_dir),
            "book_summaries_count": len(list(self.summaries_dir.glob("*.json"))),
            "markdown_files_count": len(list(self.markdown_dir.glob("*.md"))),
            "figures_count": len(list(self.figures_dir.glob("*"))) if self.figures_dir.exists() else 0
        }

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove extra spaces and limit length
        filename = '_'.join(filename.split())
        return filename[:100]  # Limit to 100 characters
