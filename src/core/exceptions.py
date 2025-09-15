"""
Custom exceptions for educational content processing.

This module defines specific exceptions used throughout the
educational content understanding and summarization pipeline.
"""


class ProcessingError(Exception):
    """Base exception for educational content processing errors."""
    pass


class ContentUnderstandingError(ProcessingError):
    """Raised when Azure Content Understanding processing fails."""
    
    def __init__(self, message: str, operation: str = None, original_error: Exception = None):
        super().__init__(message)
        self.operation = operation
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.operation:
            base_msg = f"[{self.operation}] {base_msg}"
        if self.original_error:
            base_msg += f" (caused by: {self.original_error})"
        return base_msg


class SummarizationError(ProcessingError):
    """Raised when book summarization processing fails."""
    
    def __init__(self, message: str, chapter_number: int = None, original_error: Exception = None):
        super().__init__(message)
        self.chapter_number = chapter_number
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.chapter_number:
            base_msg = f"[Chapter {self.chapter_number}] {base_msg}"
        if self.original_error:
            base_msg += f" (caused by: {self.original_error})"
        return base_msg


class DocumentProcessingError(ProcessingError):
    """Raised when document processing fails."""
    pass


class PipelineError(ProcessingError):
    """Raised when pipeline operations fail."""
    pass


class ConfigurationError(ProcessingError):
    """Raised when configuration is invalid or missing."""
    pass


class FileNotFoundError(ProcessingError):
    """Raised when required files are not found."""
    pass


class TokenLimitError(ProcessingError):
    """Raised when content exceeds token limits."""
    
    def __init__(self, message: str, token_count: int = None, limit: int = None):
        super().__init__(message)
        self.token_count = token_count
        self.limit = limit
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.token_count and self.limit:
            base_msg += f" (tokens: {self.token_count:,} > limit: {self.limit:,})"
        return base_msg
