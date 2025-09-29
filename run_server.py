#!/usr/bin/env python3
"""
Server runner for the Educational Content Understanding API.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    dotenv_loaded = load_dotenv()
    print(f"📄 Environment file loaded: {dotenv_loaded}")
    
    # Log key Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    if azure_endpoint and azure_deployment:
        print(f"🤖 Azure OpenAI Model: {azure_deployment}")
        print(f"🔗 Azure OpenAI Endpoint: {azure_endpoint}")
    else:
        print("⚠️  Azure OpenAI configuration not found in environment")
except ImportError:
    print("⚠️  python-dotenv not available, environment variables must be set manually")

import uvicorn
from src.api_server import app

if __name__ == "__main__":
    print("🚀 Starting Educational Content Understanding API...")
    print(f"📁 Content output directory: {os.getenv('CONTENT_OUTPUT_DIRECTORY', 'content/books')}")
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
