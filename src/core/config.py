"""
Configuration management for educational content processing.

This module handles environment variables, settings, and configuration
for Azure services and the educational content pipeline.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Application settings and configuration.

    Loads configuration from environment variables with sensible defaults.
    Supports both direct instantiation and loading from .env files.
    """

    def __init__(self):
        """Initialize settings from environment variables."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file, override=True)
            logger.info(f"📄 Configuration loaded from {env_file}")
        else:
            logger.warning("⚠️  No .env file found, using system environment variables")

        # Azure OpenAI settings (GPT-5-mini)
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_chat_deployment_name = os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        self.azure_openai_chat_api_version = os.getenv(
            "AZURE_OPENAI_CHAT_API_VERSION", "2024-12-01-preview")
        
        # Log Azure OpenAI configuration
        if self.azure_openai_endpoint and self.azure_openai_chat_deployment_name:
            logger.info(f"🤖 Azure OpenAI configured: {self.azure_openai_chat_deployment_name}")
            logger.info(f"🔗 Endpoint: {self.azure_openai_endpoint}")
        else:
            logger.warning("⚠️  Azure OpenAI configuration incomplete")
        self.azure_openai_embedding_deployment_name = os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        self.azure_openai_embedding_api_version = os.getenv(
            "AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-12-01-preview")

        # Azure Content Understanding settings
        self.azure_ai_service_endpoint = os.getenv("AZURE_AI_SERVICE_ENDPOINT")
        self.azure_ai_service_api_version = os.getenv(
            "AZURE_AI_SERVICE_API_VERSION", "2024-12-01-preview")

        # Azure Document Intelligence settings (uses same endpoint as AI services)
        self.azure_document_intelligence_endpoint = os.getenv(
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT") or self.azure_ai_service_endpoint
        self.azure_document_intelligence_api_version = os.getenv(
            "AZURE_DOCUMENT_INTELLIGENCE_API_VERSION", "2024-11-30")

        # Azure Search settings
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.azure_search_index_name = os.getenv(
            "AZURE_SEARCH_INDEX_NAME", "educational-content-index")

        # Processing settings
        self.max_completion_tokens = int(
            os.getenv("MAX_COMPLETION_TOKENS", "4000"))
        self.embedding_chunk_size = int(
            os.getenv("EMBEDDING_CHUNK_SIZE", "1000"))
        self.embedding_chunk_overlap = int(
            os.getenv("EMBEDDING_CHUNK_OVERLAP", "200"))

        # Output settings
        self.output_dir = os.getenv("OUTPUT_DIR", "educational_content")
        self.book_summaries_dir = os.getenv(
            "BOOK_SUMMARIES_DIR", "educational_content/book_summaries")

        # Analyzer settings
        self.analyzer_id = os.getenv(
            "ANALYZER_ID", "content-document-analyzer")
        self.analyzer_template_path = os.getenv(
            "ANALYZER_TEMPLATE_PATH", "analyzer_templates/content_document.json")

    @classmethod
    def from_env_file(cls, env_file: str = ".env") -> 'Settings':
        """Load settings from a .env file.

        Args:
            env_file: Path to the .env file

        Returns:
            Settings instance with loaded configuration
        """
        if Path(env_file).exists():
            load_dotenv(env_file, override=True)
        return cls()

    def validate(self) -> None:
        """Validate that required settings are present.

        Raises:
            ValueError: If required settings are missing
        """
        required_settings = [
            ("azure_openai_endpoint", self.azure_openai_endpoint),
            ("azure_openai_chat_deployment_name",
             self.azure_openai_chat_deployment_name),
            ("azure_ai_service_endpoint", self.azure_ai_service_endpoint)
        ]

        missing = [name for name, value in required_settings if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}")

    def get_output_paths(self) -> dict:
        """Get configured output paths.

        Returns:
            Dictionary with output path configurations
        """
        base_dir = Path(self.output_dir)
        summaries_dir = Path(self.book_summaries_dir)

        return {
            "base_dir": base_dir,
            "summaries_dir": summaries_dir,
            "markdown_dir": base_dir,
            "figures_dir": base_dir / "figures"
        }

    def __repr__(self) -> str:
        """String representation of settings (without sensitive data)."""
        return (
            f"Settings("
            f"chat_deployment={self.azure_openai_chat_deployment_name}, "
            f"ai_service_endpoint={'***' if self.azure_ai_service_endpoint else None}, "
            f"max_tokens={self.max_completion_tokens}, "
            f"output_dir={self.output_dir}"
            f")"
        )
