#!/usr/bin/env python3
"""
Server runner for the Educational Content Understanding API.
"""

from src.api_server import app
import uvicorn
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


if __name__ == "__main__":
    print("🚀 Starting Educational Content Understanding API...")
    print(
        f"📁 Content output directory: {os.getenv('CONTENT_OUTPUT_DIRECTORY', 'content/books')}")
    print("📋 Available endpoints:")
    print("   • POST /enhanced/process - Enhanced document processing")
    print("   • GET /enhanced/status/{job_id} - Job status")
    print("   • GET /enhanced/download/{job_id}/markdown - Download results")
    print("   • GET /docs - API documentation")
    print()

    uvicorn.run(
        "src.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
