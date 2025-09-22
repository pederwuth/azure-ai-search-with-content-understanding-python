# 🚀 FastAPI Book Summarization Guide

## Quick Start

1. **Start the server:**

   ```bash
   python run_server.py
   ```

2. **Open your browser to view the API documentation:**
   ```
   http://localhost:8000/docs
   ```

## Available Endpoints

### 🏥 Health Check

```bash
curl http://localhost:8000/summarization/health
```

### 📚 Summarize Content Directly

```bash
curl -X POST http://localhost:8000/summarization/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "book_title": "My Book",
    "markdown_content": "# Chapter 1\nYour content here..."
  }'
```

### 📁 Upload and Summarize File

```bash
curl -X POST http://localhost:8000/summarization/summarize-file \
  -F "file=@your_book.md" \
  -F "book_title=Optional Title"
```

## Python Usage Examples

### Using requests library:

```python
import requests

# Test the API
response = requests.post(
    "http://localhost:8000/summarization/summarize",
    json={
        "book_title": "My Book",
        "markdown_content": "# Chapter 1\nContent here..."
    }
)

result = response.json()
print(f"Summary: {result['final_summary']}")
```

### Upload a file:

```python
import requests

with open("book.md", "rb") as f:
    response = requests.post(
        "http://localhost:8000/summarization/summarize-file",
        files={"file": f},
        data={"book_title": "My Book"}
    )

result = response.json()
print(f"Book: {result['book_title']}")
print(f"Chapters: {result['total_chapters']}")
```

## Response Format

Both endpoints return JSON with this structure:

```json
{
  "success": true,
  "book_title": "Your Book Title",
  "total_chapters": 3,
  "processing_time_seconds": 25.5,
  "total_tokens_used": 0,
  "summary_id": "summary_20250919_001234",
  "final_summary": "Comprehensive book summary with key themes and learning objectives..."
}
```

## Testing

Run the test script to verify everything works:

```bash
python test_fastapi_summarizer.py
```

This will test both the health endpoint and content summarization with sample data.

## Features

✅ **Progressive Chapter Analysis** - Analyzes chapters sequentially with context  
✅ **Comprehensive Summaries** - Generates key themes and learning objectives  
✅ **File Upload Support** - Upload .md files directly  
✅ **Production Ready** - Proper error handling and validation  
✅ **RESTful Design** - Standard HTTP methods and status codes
