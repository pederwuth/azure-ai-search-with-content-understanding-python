#!/usr/bin/env python3
"""
Test version of the summarization service with mock data

This service provides the same API as the real service but uses
mock data instead of Azure OpenAI, allowing testing without
Azure credentials.
"""

import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class SummarizeRequest(BaseModel):
    book_title: str = Field(..., description="Title of the book")
    markdown_content: str = Field(..., description="Markdown content to summarize")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str

# Create FastAPI app
app = FastAPI(
    title="Book Summarization Service (Test Mode)",
    description="Test version of book summarization service with mock data",
    version="1.0.0-test",
    docs_url="/docs",
    redoc_url="/redoc"
)

class MockBookSummarizer:
    """Mock summarizer that generates realistic test data"""
    
    def create_mock_summary(self, markdown_content: str, book_title: str):
        """Create a mock book summary"""
        
        # Count chapters from markdown
        chapter_count = len([line for line in markdown_content.split('\n') if line.startswith('## ')])
        if chapter_count == 0:
            chapter_count = 1
        
        # Create mock chapter summaries
        chapter_summaries = []
        for i in range(chapter_count):
            chapter_summaries.append({
                "chapter_number": i + 1,
                "chapter_title": f"Chapter {i + 1}",
                "summary": f"This chapter covers key concepts and introduces important topics for {book_title}. It builds upon previous knowledge and sets the foundation for subsequent chapters.",
                "key_concepts": [
                    f"Concept {j + 1} from Chapter {i + 1}" for j in range(3)
                ],
                "main_topics": [
                    f"Topic {j + 1} from Chapter {i + 1}" for j in range(2)
                ],
                "token_count": 150,
                "created_at": datetime.now().isoformat()
            })
        
        # Create mock book summary
        book_summary = {
            "book_title": book_title,  # Use correct field name
            "overall_summary": f"This comprehensive guide on {book_title} provides readers with essential knowledge and practical insights. The book is structured to build understanding progressively through {chapter_count} well-organized chapters.",
            "key_themes": [
                "Foundational principles",
                "Practical applications", 
                "Best practices",
                "Real-world examples"
            ],
            "learning_objectives": [
                f"Understand the core concepts of {book_title}",
                "Apply knowledge to practical scenarios",
                "Develop problem-solving skills",
                "Build expertise in the subject area"
            ],
            "chapter_summaries": chapter_summaries,
            "total_chapters": chapter_count,
            "created_at": datetime.now().isoformat()
        }
        
        return book_summary

# Global mock summarizer
mock_summarizer = MockBookSummarizer()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="book-summarization-service-test",
        version="1.0.0-test"
    )

@app.post("/summarize")
async def summarize_content(request: SummarizeRequest):
    """Summarize markdown content (mock version)"""
    try:
        logger.info(f"Creating mock summary for book: {request.book_title}")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Generate mock summary
        book_summary = mock_summarizer.create_mock_summary(
            request.markdown_content,
            request.book_title
        )
        
        logger.info(f"✅ Successfully created mock summary for '{request.book_title}' with {len(book_summary['chapter_summaries'])} chapters")
        
        return book_summary
        
    except Exception as e:
        logger.error(f"❌ Error creating mock summary: {e}")
        raise HTTPException(status_code=500, detail=f"Mock summarization failed: {str(e)}")

@app.post("/summarize-file")
async def summarize_file(
    file: UploadFile = File(..., description="Markdown file to summarize"),
    book_title: Optional[str] = Form(None, description="Optional book title")
):
    """Upload and summarize a markdown file (mock version)"""
    
    # Validate file type
    if not file.filename or not file.filename.endswith(('.md', '.markdown', '.txt')):
        raise HTTPException(
            status_code=400, 
            detail="File must be a markdown file (.md, .markdown, or .txt)"
        )
    
    try:
        # Read file content
        content = await file.read()
        markdown_content = content.decode('utf-8')
        
        # Use provided title or derive from filename
        title = book_title or (file.filename.replace('.md', '').replace('.markdown', '').replace('.txt', '') if file.filename else "Unknown Book")
        
        logger.info(f"Creating mock summary for file: {title} (file: {file.filename})")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Generate mock summary
        book_summary = mock_summarizer.create_mock_summary(markdown_content, title)
        
        logger.info(f"✅ Successfully created mock summary for file '{file.filename}' with {len(book_summary['chapter_summaries'])} chapters")
        
        return book_summary
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
    except Exception as e:
        logger.error(f"❌ Error creating mock file summary: {e}")
        raise HTTPException(status_code=500, detail=f"Mock file summarization failed: {str(e)}")

def main():
    """Run the test summarization service"""
    print("🧪 Starting Book Summarization Service (TEST MODE)")
    print("📚 Mock service for testing without Azure credentials")
    print("🌐 Service will be available at: http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔍 Health Check: http://localhost:8001/health")
    print("⚠️  This service uses MOCK DATA - not real AI summarization")
    print()
    
    # Run with uvicorn
    uvicorn.run(
        "test_summarization_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()