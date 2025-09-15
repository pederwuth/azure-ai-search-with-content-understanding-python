"""
Content Understanding module for educational content processing.

This module provides Azure Content Understanding integration
for enhanced document processing and figure analysis.
"""

from .client import ContentUnderstandingClient
from .document_processor import DocumentProcessor

__all__ = [
    'ContentUnderstandingClient',
    'DocumentProcessor'
]
