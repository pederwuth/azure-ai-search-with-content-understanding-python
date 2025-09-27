"""
Configuration for summarization services

Provides configuration management for summarization service connections
and deployment options.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SummarizationConfig:
    """Configuration for summarization service"""

    # Service connection settings
    service_url: str = "http://localhost:8001"
    timeout: int = 300  # 5 minutes for large books

    # Deployment mode
    use_service: bool = True

    # Health check settings
    health_check_retries: int = 3
    health_check_interval: int = 5

    # Fallback behavior
    fallback_to_direct: bool = True


# Global configuration instance
config = SummarizationConfig()


def get_summarization_config() -> SummarizationConfig:
    """Get the current summarization configuration"""
    return config


def update_summarization_config(**kwargs) -> SummarizationConfig:
    """Update summarization configuration"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config
