"""
API endpoints for the educational content understanding system.
"""

from .summarization_api import router as summarization_router

__all__ = ['summarization_router']
