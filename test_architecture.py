#!/usr/bin/env python3
"""
Test script for the separated summarization architecture

This script tests:
1. Standalone summarization service (independent usage)
2. Document processor calling summarization service (integrated usage)
3. Fallback behavior when service is unavailable
"""

import sys
import time
import requests
import json
from pathlib import Path

# Test markdown content
TEST_MARKDOWN = """# Test Book: Introduction to Programming

## Chapter 1: Getting Started

Programming is the art of telling computers what to do. In this chapter, we'll explore the fundamental concepts that every programmer should know.

### What is Programming?

Programming involves writing instructions that a computer can understand and execute. These instructions are written in programming languages.

### Why Learn Programming?

- Problem solving skills
- Creative expression
- Career opportunities
- Understanding technology

## Chapter 2: Basic Concepts

Now that we understand what programming is, let's dive into some basic concepts.

### Variables

Variables are containers for storing data values. They allow us to give names to pieces of information.

### Functions

Functions are reusable blocks of code that perform specific tasks. They help organize our code and make it more maintainable.

## Chapter 3: Next Steps

With these fundamentals in hand, you're ready to start your programming journey.

### Practice Projects

- Build a calculator
- Create a simple game
- Write a web scraper

### Resources

- Online tutorials
- Programming books
- Coding communities
"""

def test_standalone_service():
    """Test the standalone summarization service"""
    print("🧪 Testing Standalone Summarization Service")
    print("=" * 50)
    
    # Test health check
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Check: {health_data['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to summarization service: {e}")
        print("💡 Make sure to start the service with: python summarization_service.py")
        return False
    
    # Test summarization
    try:
        print("📚 Testing content summarization...")
        
        payload = {
            "book_title": "Test Book: Introduction to Programming",
            "markdown_content": TEST_MARKDOWN
        }
        
        response = requests.post(
            "http://localhost:8001/summarize",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully summarized book!")
            print(f"   📖 Title: {result.get('title', 'N/A')}")
            print(f"   📝 Chapters: {len(result.get('chapter_summaries', []))}")
            print(f"   🎯 Themes: {len(result.get('key_themes', []))}")
            print(f"   🎓 Objectives: {len(result.get('learning_objectives', []))}")
            return True
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Summarization request failed: {e}")
        return False

def test_integrated_usage():
    """Test the document processor using summarization service"""
    print("\n🧪 Testing Integrated Usage (Document Processor → Summarization Service)")
    print("=" * 70)
    
    try:
        # Import the summarization factory
        sys.path.append(str(Path(__file__).parent / "src"))
        from src.summarization.factory import get_summarization_factory
        
        print("📚 Testing summarization factory...")
        
        # Get the factory
        factory = get_summarization_factory()
        
        # Test summarization
        book_summary = factory.summarize_markdown(
            TEST_MARKDOWN,
            "Test Book: Introduction to Programming"
        )
        
        print(f"✅ Successfully used summarization factory!")
        print(f"   📖 Title: {book_summary.title}")
        print(f"   📝 Chapters: {len(book_summary.chapter_summaries)}")
        print(f"   🎯 Themes: {len(book_summary.key_themes)}")
        print(f"   🎓 Objectives: {len(book_summary.learning_objectives)}")
        
        # Show some details
        if book_summary.chapter_summaries:
            first_chapter = book_summary.chapter_summaries[0]
            print(f"   📄 First chapter: {first_chapter.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated usage test failed: {e}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when service is unavailable"""
    print("\n🧪 Testing Fallback Behavior (Service Unavailable)")
    print("=" * 55)
    
    try:
        # Import and configure for direct mode
        sys.path.append(str(Path(__file__).parent / "src"))
        from src.summarization.config import update_summarization_config
        from src.summarization.factory import get_summarization_factory
        
        print("⚙️ Configuring for direct mode (no service)...")
        
        # Configure to not use service
        update_summarization_config(use_service=False)
        
        # Get a fresh factory
        factory = get_summarization_factory()
        factory.reset_service_cache()
        
        # Test summarization
        book_summary = factory.summarize_markdown(
            TEST_MARKDOWN,
            "Test Book: Introduction to Programming"
        )
        
        print(f"✅ Fallback to direct mode successful!")
        print(f"   📖 Title: {book_summary.title}")
        print(f"   📝 Chapters: {len(book_summary.chapter_summaries)}")
        print("   💡 Used direct imports instead of service")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

def test_file_upload():
    """Test file upload to standalone service"""
    print("\n🧪 Testing File Upload to Standalone Service")
    print("=" * 50)
    
    # Create a test file
    test_file = Path("test_book.md")
    test_file.write_text(TEST_MARKDOWN)
    
    try:
        print("📁 Testing file upload...")
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_book.md', f, 'text/markdown')}
            data = {'book_title': 'Test Book from File'}
            
            response = requests.post(
                "http://localhost:8001/summarize-file",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ File upload and summarization successful!")
            print(f"   📖 Title: {result.get('title', 'N/A')}")
            print(f"   📝 Chapters: {len(result.get('chapter_summaries', []))}")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()

def main():
    """Run all tests"""
    print("🔬 SUMMARIZATION ARCHITECTURE TESTS")
    print("=" * 60)
    print("Testing the separated summarization architecture:")
    print("• Standalone service (independent usage)")
    print("• Integrated usage (document processor → service)")
    print("• Fallback behavior")
    print("• File upload")
    print()
    
    results = []
    
    # Test 1: Standalone service
    results.append(("Standalone Service", test_standalone_service()))
    
    # Test 2: File upload
    results.append(("File Upload", test_file_upload()))
    
    # Test 3: Integrated usage
    results.append(("Integrated Usage", test_integrated_usage()))
    
    # Test 4: Fallback behavior
    results.append(("Fallback Behavior", test_fallback_behavior()))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("Your separated summarization architecture is working correctly!")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    print("\n💡 Usage Tips:")
    print("• Start standalone service: python summarization_service.py")
    print("• Start both services: python start_services.py both") 
    print("• Use factory in code: from src.summarization.factory import get_summarization_factory")

if __name__ == "__main__":
    main()