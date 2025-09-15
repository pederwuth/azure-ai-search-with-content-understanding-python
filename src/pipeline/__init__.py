"""
Pipeline module for educational content processing.

This module provides high-level pipelines that combine various AI services
for comprehensive educational content processing workflows.
"""

from .content_understanding_pipeline import (
    ContentUnderstandingPipeline,
    process_pdf_with_content_understanding
)

__all__ = [
    'ContentUnderstandingPipeline',
    'process_pdf_with_content_understanding'
]
