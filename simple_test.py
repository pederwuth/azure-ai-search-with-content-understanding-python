#!/usr/bin/env python3
"""
Simple test of the summarization architecture
"""

import requests
import sys
from pathlib import Path


def test_standalone_service():
    """Test the standalone service"""
    print("🧪 Testing Standalone Service...")

    try:
        # Test health
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False

    # Test summarization
    try:
        payload = {
            "book_title": "Architecture Test Book",
            "markdown_content": "# Chapter 1: Introduction\nThis is a test.\n\n## Chapter 2: Details\nMore content here."
        }

        response = requests.post(
            "http://localhost:8001/summarize", json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Summarization successful!")
            print(f"   📖 Title: {result.get('title')}")
            print(f"   📝 Chapters: {len(result.get('chapter_summaries', []))}")
            return True
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Summarization error: {e}")
        return False


def test_factory_direct_mode():
    """Test the factory in direct mode"""
    print("\n🧪 Testing Factory (Direct Mode)...")

    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from src.summarization.config import update_summarization_config
        from src.summarization.factory import get_summarization_factory

        # Configure for direct mode
        update_summarization_config(use_service=False)

        # Get factory
        factory = get_summarization_factory()
        factory.reset_service_cache()

        # Test markdown content
        test_content = "# Chapter 1: Introduction\nThis is a test.\n\n## Chapter 2: Details\nMore content here."

        # This should use direct imports
        book_summary = factory.summarize_markdown(
            test_content, "Factory Test Book")

        print(f"✅ Direct mode successful!")
        print(f"   📖 Title: {book_summary.book_title}")
        print(f"   📝 Chapters: {len(book_summary.chapter_summaries)}")
        return True

    except Exception as e:
        print(f"❌ Direct mode error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_service_mode():
    """Test the factory in service mode"""
    print("\n🧪 Testing Factory (Service Mode)...")

    try:
        sys.path.append(str(Path(__file__).parent / "src"))
        from src.summarization.config import update_summarization_config
        from src.summarization.factory import get_summarization_factory

        # Configure for service mode
        update_summarization_config(
            use_service=True, service_url="http://localhost:8001")

        # Get fresh factory
        factory = get_summarization_factory()
        factory.reset_service_cache()

        # Test markdown content
        test_content = "# Chapter 1: Introduction\nThis is a test.\n\n## Chapter 2: Details\nMore content here."

        # This should use the service
        book_summary = factory.summarize_markdown(
            test_content, "Service Test Book")

        print(f"✅ Service mode successful!")
        print(f"   📖 Title: {book_summary.book_title}")
        print(f"   📝 Chapters: {len(book_summary.chapter_summaries)}")
        return True

    except Exception as e:
        print(f"❌ Service mode error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔬 SIMPLIFIED ARCHITECTURE TESTS")
    print("=" * 40)

    results = []

    # Test standalone service
    results.append(("Standalone Service", test_standalone_service()))

    # Test factory direct mode
    results.append(("Factory Direct Mode", test_factory_direct_mode()))

    # Test factory service mode
    results.append(("Factory Service Mode", test_factory_service_mode()))

    # Summary
    print("\n📊 RESULTS")
    print("=" * 20)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("Your separated architecture is working!")
    else:
        print("\n⚠️ Some tests failed.")


if __name__ == "__main__":
    main()
