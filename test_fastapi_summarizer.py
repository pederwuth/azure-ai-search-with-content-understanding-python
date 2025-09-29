#!/usr/bin/env python3
"""
FastAPI Book Summarization API Usage Examples

This script demonstrates how to use the book summarization endpoints.
"""

import requests
import json
import sys
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8000"


def test_health():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/summarization/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed:", response.json())
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def summarize_content(title, markdown_content):
    """Summarize markdown content directly"""
    print(f"📚 Summarizing content: {title}")

    data = {
        "book_title": title,
        "markdown_content": markdown_content
    }

    try:
        response = requests.post(
            f"{BASE_URL}/summarization/summarize",
            json=data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Summarization successful!")
            print(f"📖 Book Title: {result['book_title']}")
            print(f"📚 Total Chapters: {result['total_chapters']}")
            print(f"📝 Summary Preview: {result['final_summary'][:200]}...")
            print(f"🆔 Summary ID: {result['summary_id']}")
            return result
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Summarization error: {e}")
        return None


def summarize_file(file_path, title=None):
    """Summarize a markdown file"""
    print(f"📁 Summarizing file: {file_path}")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'book_title': title} if title else {}

            response = requests.post(
                f"{BASE_URL}/summarization/summarize-file",
                files=files,
                data=data,
                timeout=60
            )

        if response.status_code == 200:
            result = response.json()
            print("✅ File summarization successful!")
            print(f"📖 Book Title: {result['book_title']}")
            print(f"📚 Total Chapters: {result['total_chapters']}")
            print(f"📝 Summary Preview: {result['final_summary'][:200]}...")
            return result
        else:
            print(f"❌ File summarization failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ File summarization error: {e}")
        return None


def main():
    """Main demonstration"""
    print("🚀 FastAPI Book Summarization Demo")
    print("=" * 50)

    # Test 1: Health check
    if not test_health():
        print("❌ Server not available. Make sure to run: python run_server.py")
        return

    print("\n" + "=" * 50)

    # Test 2: Summarize sample content
    sample_content = """# Chapter 1: Introduction to Python

Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.

## Why Python?

Python's design philosophy emphasizes code readability with its notable use of significant whitespace. Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.

## Key Features

- Easy to learn and use
- Extensive standard library
- Cross-platform compatibility
- Large community support

# Chapter 2: Getting Started

This chapter covers the basics of setting up Python and writing your first program.

## Installation

Python can be downloaded from the official website and is available for Windows, macOS, and Linux.

## Your First Program

The traditional first program is "Hello, World!":

```python
print("Hello, World!")
```

This simple program demonstrates Python's straightforward syntax.

# Chapter 3: Basic Concepts

Understanding variables, data types, and control structures is essential for Python programming.

## Variables and Data Types

Python supports various data types including integers, floats, strings, and booleans.

## Control Structures

Python provides if statements, loops, and functions to control program flow.
"""

    result = summarize_content("Python Programming Guide", sample_content)

    if result:
        print("\n🎯 Full Results:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
