"""
Internal summarization handler for direct calls within the same process.

This module provides a way for the document processor to call
summarization directly without HTTP when running in the same service.
"""

import logging
from typing import Optional

# Summarization components
try:
    from .book_summarizer import ProgressiveBookSummarizer
    from .models import BookSummary
    SUMMARIZATION_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import summarization components: {e}")
    SUMMARIZATION_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global summarizer instance
_summarizer = None


def get_internal_summarizer() -> Optional[ProgressiveBookSummarizer]:
    """Get or create the internal summarizer instance"""
    global _summarizer
    if _summarizer is None and SUMMARIZATION_AVAILABLE:
        _summarizer = ProgressiveBookSummarizer()
    return _summarizer


async def summarize_markdown_internal(markdown_content: str, title: str) -> BookSummary:
    """
    Summarize markdown content directly within the same process.

    This function is used by the factory when both the document processor
    and summarization service are running in the same process.

    Args:
        markdown_content: The markdown content to summarize
        title: The title of the document

    Returns:
        BookSummary object with the summarization results

    Raises:
        RuntimeError: If summarization is not available
        Exception: If summarization fails
    """
    if not SUMMARIZATION_AVAILABLE:
        raise RuntimeError(
            "Summarization service is not available. Please check Azure OpenAI configuration.")

    summarizer = get_internal_summarizer()
    if not summarizer:
        raise RuntimeError("Failed to initialize summarization service")

    logger.info(f"Starting internal summarization for: {title}")

    try:
        # Process the markdown content directly
        import asyncio
        book_summary = await asyncio.to_thread(
            summarizer.process_document_progressively,
            markdown_content,
            title
        )

        logger.info(f"Completed internal summarization for: {title}")
        return book_summary

    except Exception as e:
        logger.error(f"Error during internal summarization: {str(e)}")
        raise


def is_summarization_available() -> bool:
    """Check if summarization is available in this process"""
    return SUMMARIZATION_AVAILABLE and get_internal_summarizer() is not None
