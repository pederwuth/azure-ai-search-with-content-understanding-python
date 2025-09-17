"""
Azure Content Understanding client wrapper.

This module provides a clean interface to the Azure Content Understanding API
with proper error handling and logging.
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from ..core.exceptions import ContentUnderstandingError

logger = logging.getLogger(__name__)


class ContentUnderstandingClient:
    """Wrapper for Azure Content Understanding API with enhanced error handling."""

    def __init__(
        self,
        endpoint: str,
        api_version: str,
        token_provider: Callable[[], str],
        x_ms_useragent: str = "educational-content-processing"
    ):
        """Initialize Content Understanding client.

        Args:
            endpoint: Azure AI Service endpoint
            api_version: API version to use
            token_provider: Function that returns Azure AD token
            x_ms_useragent: User agent string for telemetry
        """
        # Store configuration
        self.endpoint = endpoint
        self.api_version = api_version
        self.token_provider = token_provider
        self.x_ms_useragent = x_ms_useragent

        try:
            # Import the original client from the python directory
            import sys
            sys.path.append(
                str(Path(__file__).parent.parent.parent / "python"))
            from content_understanding_client import AzureContentUnderstandingClient

            self._client = AzureContentUnderstandingClient(
                endpoint=endpoint,
                api_version=api_version,
                token_provider=token_provider,
                x_ms_useragent=x_ms_useragent
            )
            logger.info(
                "Content Understanding client initialized successfully")

        except Exception as e:
            raise ContentUnderstandingError(
                "Failed to initialize Content Understanding client",
                operation="initialization",
                original_error=e
            )

    def create_analyzer(self, analyzer_id: str, template_path: str) -> Dict[str, Any]:
        """Create a new content understanding analyzer.

        Args:
            analyzer_id: Unique ID for the analyzer
            template_path: Path to analyzer template JSON file

        Returns:
            Analyzer creation result

        Raises:
            ContentUnderstandingError: If analyzer creation fails
        """
        try:
            logger.info(f"Creating analyzer: {analyzer_id}")
            response = self._client.begin_create_analyzer(
                analyzer_id,
                analyzer_template_path=template_path
            )
            result = self._client.poll_result(response)

            logger.info(f"Analyzer created successfully: {analyzer_id}")
            return result

        except Exception as e:
            raise ContentUnderstandingError(
                f"Failed to create analyzer: {analyzer_id}",
                operation="create_analyzer",
                original_error=e
            )

    def analyze_image(self, analyzer_id: str, image_path: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Analyze an image using the specified analyzer.

        Args:
            analyzer_id: ID of the analyzer to use
            image_path: Path to the image file
            timeout_seconds: Maximum time to wait for analysis

        Returns:
            Analysis result

        Raises:
            ContentUnderstandingError: If analysis fails
        """
        try:
            logger.debug(
                f"Analyzing image: {image_path} with analyzer: {analyzer_id}")
            response = self._client.begin_analyze(analyzer_id, image_path)
            result = self._client.poll_result(
                response, timeout_seconds=timeout_seconds)

            logger.debug(f"Image analysis completed: {image_path}")
            return result

        except Exception as e:
            raise ContentUnderstandingError(
                f"Failed to analyze image: {image_path}",
                operation="analyze_image",
                original_error=e
            )

    def delete_analyzer(self, analyzer_id: str) -> None:
        """Delete an analyzer.

        Args:
            analyzer_id: ID of the analyzer to delete

        Raises:
            ContentUnderstandingError: If deletion fails
        """
        try:
            logger.info(f"Deleting analyzer: {analyzer_id}")
            self._client.delete_analyzer(analyzer_id)
            logger.info(f"Analyzer deleted successfully: {analyzer_id}")

        except Exception as e:
            raise ContentUnderstandingError(
                f"Failed to delete analyzer: {analyzer_id}",
                operation="delete_analyzer",
                original_error=e
            )

    def get_analyzer_details(self, analyzer_id: str) -> Dict[str, Any]:
        """Get details of an analyzer.

        Args:
            analyzer_id: ID of the analyzer

        Returns:
            Analyzer details

        Raises:
            ContentUnderstandingError: If retrieval fails
        """
        try:
            result = self._client.get_analyzer_detail_by_id(analyzer_id)
            return result

        except Exception as e:
            raise ContentUnderstandingError(
                f"Failed to get analyzer details: {analyzer_id}",
                operation="get_analyzer_details",
                original_error=e
            )
