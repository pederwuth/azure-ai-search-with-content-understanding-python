#!/usr/bin/env python3
"""
Complete FastAPI Book Summarization Usage Examples

This script shows you exactly how to use the book summarization API endpoints.
Run this after starting the server with: python run_server.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def check_server():
    """Check if the server is running"""
    print("🔍 Checking if FastAPI server is running...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=3)
        print("✅ Server is running!")
        return True
    except:
        print("❌ Server not running. Please start it with: python run_server.py")
        return False


def example_1_health_check():
    """Example 1: Health check"""
    print("\n" + "="*60)
    print("📋 EXAMPLE 1: Health Check")
    print("="*60)

    print("🏥 Testing health endpoint...")
    print("📡 Request: GET /summarization/health")

    try:
        response = requests.get(f"{BASE_URL}/summarization/health")
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_summarize_content():
    """Example 2: Summarize content directly"""
    print("\n" + "="*60)
    print("📋 EXAMPLE 2: Summarize Content Directly")
    print("="*60)

    # Sample markdown content
    content = '''# Chapter 1: Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to automatically learn and improve from experience without being explicitly programmed.

## Types of Machine Learning

There are three main types of machine learning:

### Supervised Learning
Learning with labeled training data to make predictions on new data.

### Unsupervised Learning  
Finding hidden patterns in data without labeled examples.

### Reinforcement Learning
Learning through trial and error with rewards and penalties.

# Chapter 2: Getting Started

This chapter covers the practical steps to begin your machine learning journey.

## Tools and Libraries

Popular Python libraries include:
- Scikit-learn for general machine learning
- TensorFlow and PyTorch for deep learning
- Pandas for data manipulation
- NumPy for numerical computing

## Your First Model

Start with simple algorithms like linear regression before moving to complex models.
'''

    data = {
        "book_title": "Machine Learning Basics",
        "markdown_content": content
    }

    print("📚 Summarizing book content...")
    print("📡 Request: POST /summarization/summarize")
    print(f"📄 Content length: {len(content)} characters")

    try:
        response = requests.post(
            f"{BASE_URL}/summarization/summarize",
            json=data,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📖 Book Title: {result['book_title']}")
            print(f"📚 Total Chapters: {result['total_chapters']}")
            print(f"🆔 Summary ID: {result['summary_id']}")
            print(f"📝 Summary Preview:")
            print(result['final_summary'][:400] + "...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:300])

    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_file_upload():
    """Example 3: Upload and summarize a markdown file"""
    print("\n" + "="*60)
    print("📋 EXAMPLE 3: File Upload (Conceptual)")
    print("="*60)

    print("📁 To upload a markdown file, you would use:")
    print("📡 Request: POST /summarization/summarize-file")
    print("📄 Form data: file=@your_book.md")
    print("")
    print("🐍 Python example:")
    print("""
with open('your_book.md', 'rb') as f:
    files = {'file': f}
    data = {'book_title': 'Your Book Title'}
    response = requests.post(
        'http://localhost:8000/summarization/summarize-file',
        files=files,
        data=data
    )
""")

    print("💻 cURL example:")
    print("""
curl -X POST http://localhost:8000/summarization/summarize-file \\
  -F "file=@your_book.md" \\
  -F "book_title=Your Book Title"
""")


def example_4_api_docs():
    """Example 4: Access API documentation"""
    print("\n" + "="*60)
    print("📋 EXAMPLE 4: API Documentation")
    print("="*60)

    print("📖 Interactive API documentation is available at:")
    print("🌐 http://localhost:8000/docs")
    print("")
    print("This provides a complete interface to test all endpoints!")


def main():
    """Run all examples"""
    print("🚀 FastAPI Book Summarization - Complete Usage Guide")
    print("=" * 60)

    if not check_server():
        print("\n🔧 To start the server:")
        print("   1. Open a terminal")
        print("   2. Run: python run_server.py")
        print("   3. Wait for 'Application startup complete'")
        print("   4. Run this script again")
        return

    # Run all examples
    example_1_health_check()
    example_2_summarize_content()
    example_3_file_upload()
    example_4_api_docs()

    print("\n" + "="*60)
    print("🎉 FASTAPI USAGE EXAMPLES COMPLETE!")
    print("="*60)
    print("✅ Your FastAPI book summarization service is ready to use!")
    print("📚 You can now summarize any markdown content via HTTP API")
    print("🌐 Visit http://localhost:8000/docs for interactive documentation")


if __name__ == "__main__":
    main()
