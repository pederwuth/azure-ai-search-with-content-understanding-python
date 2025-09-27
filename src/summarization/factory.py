"""
Summarization Factory

Provides a unified interface that can use either:
1. Internal summarization (when running in the same process)
2. Standalone summarization service (via HTTP API)
3. Direct imports (fallback)
"""

import logging
import time
from typing import Optional, Union
from pathlib import Path

from .config import get_summarization_config
from .client import SummarizationServiceClient
from .book_summarizer import ProgressiveBookSummarizer
from ..summarization.models import BookSummary

# Try to import internal summarization
try:
    from .internal import summarize_markdown_internal, is_summarization_available
    INTERNAL_SUMMARIZATION_AVAILABLE = True
except ImportError:
    INTERNAL_SUMMARIZATION_AVAILABLE = False

logger = logging.getLogger(__name__)


class SummarizationFactory:
    """
    Factory that provides summarization capabilities via service or direct imports

    This factory automatically chooses between:
    1. Standalone summarization service (via HTTP API)
    2. Direct imports (fallback or when configured)

    The choice depends on configuration and service availability.
    """

    def __init__(self):
        """Initialize the summarization factory"""
        self.config = get_summarization_config()
        self._client: Optional[SummarizationServiceClient] = None
        self._direct_summarizer: Optional[ProgressiveBookSummarizer] = None
        self._service_available: Optional[bool] = None

        logger.info("Initialized SummarizationFactory")

    def _get_client(self) -> SummarizationServiceClient:
        """Get or create the service client"""
        if self._client is None:
            self._client = SummarizationServiceClient(
                base_url=self.config.service_url,
                timeout=self.config.timeout
            )
        return self._client

    def _get_direct_summarizer(self) -> ProgressiveBookSummarizer:
        """Get or create the direct summarizer"""
        if self._direct_summarizer is None:
            logger.info("Initializing direct ProgressiveBookSummarizer...")
            self._direct_summarizer = ProgressiveBookSummarizer()
        return self._direct_summarizer

    def _check_service_availability(self) -> bool:
        """
        Check if the summarization service is available

        Returns:
            True if service is available and healthy
        """
        if not self.config.use_service:
            return False

        # Use cached result if recent
        if self._service_available is not None:
            return self._service_available

        try:
            client = self._get_client()

            # Try health check with retries
            for attempt in range(self.config.health_check_retries):
                try:
                    if client.is_service_available():
                        logger.info("✅ Summarization service is available")
                        self._service_available = True
                        return True
                except Exception as e:
                    logger.warning(
                        f"Health check attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.health_check_retries - 1:
                        time.sleep(self.config.health_check_interval)

            logger.warning(
                "❌ Summarization service is not available after retries")
            self._service_available = False
            return False

        except Exception as e:
            logger.error(f"❌ Error checking service availability: {e}")
            self._service_available = False
            return False

    def _should_use_service(self) -> bool:
        """
        Determine whether to use the service or direct imports

        Returns:
            True if should use service, False for direct imports
        """
        if not self.config.use_service:
            logger.info("📍 Using direct imports (service disabled in config)")
            return False

        if self._check_service_availability():
            logger.info("📍 Using standalone summarization service")
            return True

        if self.config.fallback_to_direct:
            logger.info(
                "📍 Falling back to direct imports (service unavailable)")
            return False

        raise RuntimeError(
            "Summarization service unavailable and fallback disabled")

    def summarize_markdown(self, markdown_content: str, book_title: str) -> BookSummary:
        """
        Summarize markdown content using the best available method

        Args:
            markdown_content: The markdown content to summarize
            book_title: Title of the book

        Returns:
            BookSummary: The summarized book
        """
        if self._should_use_service():
            try:
                client = self._get_client()
                return client.summarize_markdown(markdown_content, book_title)
            except Exception as e:
                logger.error(f"❌ Service call failed: {e}")
                if self.config.fallback_to_direct:
                    logger.info("🔄 Falling back to direct imports")
                    # Mark service as unavailable for future calls
                    self._service_available = False
                else:
                    raise

        # Use direct imports
        summarizer = self._get_direct_summarizer()
        return summarizer.process_document_progressively(markdown_content, book_title)

    def summarize_file(self, file_path: Union[str, Path], book_title: Optional[str] = None) -> BookSummary:
        """
        Summarize a markdown file using the best available method

        Args:
            file_path: Path to the markdown file
            book_title: Optional book title

        Returns:
            BookSummary: The summarized book
        """
        file_path = Path(file_path)

        if self._should_use_service():
            try:
                client = self._get_client()
                return client.summarize_file(str(file_path), book_title)
            except Exception as e:
                logger.error(f"❌ Service call failed: {e}")
                if self.config.fallback_to_direct:
                    logger.info("🔄 Falling back to direct imports")
                    # Mark service as unavailable for future calls
                    self._service_available = False
                else:
                    raise

        # Use direct imports - read file and process
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        title = book_title or file_path.stem
        summarizer = self._get_direct_summarizer()
        return summarizer.process_document_progressively(markdown_content, title)

    async def summarize_markdown_async(self, markdown_content: str, book_title: str) -> BookSummary:
        """
        Async version of summarize_markdown

        Uses internal summarization if available, otherwise falls back to service or direct.

        Args:
            markdown_content: The markdown content to summarize
            book_title: Title of the book

        Returns:
            BookSummary: The summarized book
        """
        # Try internal summarization first (when running in the same process)
        if INTERNAL_SUMMARIZATION_AVAILABLE and is_summarization_available():
            logger.info("🔧 Using internal summarization (same process)")
            return await summarize_markdown_internal(markdown_content, book_title)

        # Fall back to external service or direct
        import asyncio
        return await asyncio.to_thread(self.summarize_markdown, markdown_content, book_title)

    async def summarize_file_async(self, file_path: Union[str, Path], book_title: Optional[str] = None) -> BookSummary:
        """
        Async version of summarize_file

        Args:
            file_path: Path to the markdown file
            book_title: Optional book title

        Returns:
            BookSummary: The summarized book
        """
        import asyncio
        return await asyncio.to_thread(self.summarize_file, file_path, book_title)

    def reset_service_cache(self):
        """Reset the service availability cache"""
        self._service_available = None
        logger.info("🔄 Reset service availability cache")


# Global factory instance
_factory: Optional[SummarizationFactory] = None


def get_summarization_factory() -> SummarizationFactory:
    """Get the global summarization factory instance"""
    global _factory
    if _factory is None:
        _factory = SummarizationFactory()
    return _factory
