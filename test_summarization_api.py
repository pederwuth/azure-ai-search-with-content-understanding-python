#!/usr/bin/env python3
"""
Test script for the new book summarization API.
"""

import requests
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_MARKDOWN = """
# Chapter 1: Introduction

This is the first chapter of our test book. It introduces the main concepts and sets the stage for what's to come.

The introduction covers basic principles and provides background context necessary for understanding later chapters.

# Chapter 2: Core Concepts

Building on the introduction, this chapter dives deeper into the core concepts that form the foundation of our subject matter.

We explore theoretical frameworks and practical applications that will be referenced throughout the book.

# Chapter 3: Advanced Topics

This final chapter examines advanced topics and complex scenarios that build upon everything learned in previous chapters.

The advanced material demonstrates how core concepts can be applied to solve real-world problems.
"""


def test_summarization_api():
    """Test the book summarization API."""
    print("🧪 Testing Book Summarization API")

    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/summarization/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return

    # Test summarization
    print("2. Testing book summarization...")
    try:
        payload = {
            "book_title": "Test Book: A Sample Study",
            "markdown_content": TEST_MARKDOWN
        }

        response = requests.post(
            f"{BASE_URL}/summarization/summarize",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Summarization successful!")
            print(f"   📚 Book: {result['book_title']}")
            print(f"   📖 Chapters: {result['total_chapters']}")
            print(f"   ⏱️  Time: {result['processing_time_seconds']:.2f}s")
            print(f"   🎯 Tokens: {result['total_tokens_used']}")
            print(f"   📝 Summary length: {len(result['final_summary'])} chars")
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Summarization error: {e}")


if __name__ == "__main__":
    test_summarization_api()
