"""
Summarization Service Client

A client for calling the standalone book summarization service.
This allows other services (like the document processor) to use summarization
via HTTP API calls rather than direct imports.
"""

import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import json

from .models import BookSummary

logger = logging.getLogger(__name__)

class SummarizationServiceClient:
    """
    Client for calling the standalone book summarization service
    
    This client provides a clean interface for other services to use
    book summarization capabilities via HTTP API calls.
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", timeout: int = 300):
        """
        Initialize the summarization service client
        
        Args:
            base_url: Base URL of the summarization service
            timeout: Request timeout in seconds (default 5 minutes for large books)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"Initialized SummarizationServiceClient with base_url: {base_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the summarization service is healthy
        
        Returns:
            Dict containing health status information
            
        Raises:
            requests.RequestException: If service is unreachable
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def is_service_available(self) -> bool:
        """
        Check if the summarization service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            health = self.health_check()
            return health.get("status") == "healthy"
        except:
            return False
    
    def summarize_markdown(self, markdown_content: str, book_title: str) -> BookSummary:
        """
        Summarize markdown content using the remote service
        
        Args:
            markdown_content: The markdown content to summarize
            book_title: Title of the book
            
        Returns:
            BookSummary: The summarized book
            
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response is invalid
        """
        try:
            logger.info(f"Sending summarization request for book: {book_title}")
            
            payload = {
                "book_title": book_title,
                "markdown_content": markdown_content
            }
            
            response = requests.post(
                f"{self.base_url}/summarize",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Convert response back to BookSummary object
            # Since it's a dataclass, we need to handle datetime parsing
            from datetime import datetime
            from .models import BookSummary, ChapterSummary
            
            # Convert datetime strings and rebuild objects properly
            chapter_summaries = []
            for cs_data in result.get('chapter_summaries', []):
                # Parse datetime
                if 'created_at' in cs_data and isinstance(cs_data['created_at'], str):
                    cs_data['created_at'] = datetime.fromisoformat(cs_data['created_at'].replace('Z', '+00:00'))
                
                # Create ChapterSummary object
                chapter_summaries.append(ChapterSummary(**cs_data))
            
            # Parse main created_at
            if 'created_at' in result and isinstance(result['created_at'], str):
                result['created_at'] = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
            
            # Create BookSummary object with proper chapter summaries
            book_summary = BookSummary(
                book_title=result['book_title'],
                overall_summary=result['overall_summary'],
                chapter_summaries=chapter_summaries,
                key_themes=result['key_themes'],
                learning_objectives=result['learning_objectives'],
                total_chapters=result['total_chapters'],
                created_at=result['created_at']
            )
            
            logger.info(f"✅ Successfully received summary for '{book_title}' with {len(book_summary.chapter_summaries)} chapters")
            return book_summary
            
        except requests.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error processing response: {e}")
            raise ValueError(f"Invalid response from summarization service: {e}")
    
    def summarize_file(self, file_path: str, book_title: Optional[str] = None) -> BookSummary:
        """
        Summarize a markdown file using the remote service
        
        Args:
            file_path: Path to the markdown file
            book_title: Optional book title (uses filename if not provided)
            
        Returns:
            BookSummary: The summarized book
            
        Raises:
            FileNotFoundError: If file doesn't exist
            requests.RequestException: If API call fails
            ValueError: If response is invalid
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            logger.info(f"Sending file summarization request for: {file_path}")
            
            # Prepare file for upload
            with open(file_path_obj, 'rb') as f:
                files = {'file': (file_path_obj.name, f, 'text/markdown')}
                data = {}
                
                if book_title:
                    data['book_title'] = book_title
                
                response = requests.post(
                    f"{self.base_url}/summarize-file",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Convert response back to BookSummary object
            # Since it's a dataclass, we need to handle datetime parsing
            from datetime import datetime
            from .models import BookSummary, ChapterSummary
            
            # Convert datetime strings and rebuild objects properly
            chapter_summaries = []
            for cs_data in result.get('chapter_summaries', []):
                # Parse datetime
                if 'created_at' in cs_data and isinstance(cs_data['created_at'], str):
                    cs_data['created_at'] = datetime.fromisoformat(cs_data['created_at'].replace('Z', '+00:00'))
                
                # Create ChapterSummary object
                chapter_summaries.append(ChapterSummary(**cs_data))
            
            # Parse main created_at
            if 'created_at' in result and isinstance(result['created_at'], str):
                result['created_at'] = datetime.fromisoformat(result['created_at'].replace('Z', '+00:00'))
            
            # Create BookSummary object with proper chapter summaries
            book_summary = BookSummary(
                book_title=result['book_title'],
                overall_summary=result['overall_summary'],
                chapter_summaries=chapter_summaries,
                key_themes=result['key_themes'],
                learning_objectives=result['learning_objectives'],
                total_chapters=result['total_chapters'],
                created_at=result['created_at']
            )
            
            logger.info(f"✅ Successfully received summary for file '{file_path_obj.name}' with {len(book_summary.chapter_summaries)} chapters")
            return book_summary
            
        except requests.RequestException as e:
            logger.error(f"❌ File upload API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error processing file response: {e}")
            raise ValueError(f"Invalid response from summarization service: {e}")
    
    async def summarize_markdown_async(self, markdown_content: str, book_title: str) -> BookSummary:
        """
        Async version of summarize_markdown
        
        Args:
            markdown_content: The markdown content to summarize
            book_title: Title of the book
            
        Returns:
            BookSummary: The summarized book
        """
        import asyncio
        return await asyncio.to_thread(self.summarize_markdown, markdown_content, book_title)
    
    async def summarize_file_async(self, file_path: str, book_title: Optional[str] = None) -> BookSummary:
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