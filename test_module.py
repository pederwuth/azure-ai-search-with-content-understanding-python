#!/usr/bin/env python3
"""
Test script for the educational content processing module.

This script demonstrates the basic functionality of the core models
and validates that the module structure is working correctly.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.core.models import BookChapter, ChapterSummary, BookSummary
from src.core.config import Settings
from src.storage.file_manager import FileManager
from src.storage.json_serializer import JsonSerializer


def test_models():
    """Test the core data models."""
    print("🧪 Testing Core Models...")
    
    # Test BookChapter
    chapter = BookChapter(
        chapter_number=1,
        title="Introduction",
        content="This is the introduction chapter with some sample content.",
        token_count=10,
        page_range="Pages 1-5"
    )
    print(f"✅ BookChapter created: {chapter.title}")
    
    # Test ChapterSummary
    chapter_summary = ChapterSummary(
        chapter_number=1,
        chapter_title="Introduction",
        summary="This chapter introduces the main concepts.",
        key_concepts=["concept1", "concept2"],
        main_topics=["topic1", "topic2"],
        token_count=8,
        created_at=datetime.now()
    )
    print(f"✅ ChapterSummary created: {chapter_summary.chapter_title}")
    
    # Test BookSummary
    book_summary = BookSummary(
        book_title="Test Book",
        overall_summary="This is a test book summary.",
        chapter_summaries=[chapter_summary],
        key_themes=["theme1", "theme2"],
        learning_objectives=["objective1", "objective2"],
        total_chapters=1,
        created_at=datetime.now()
    )
    print(f"✅ BookSummary created: {book_summary.book_title}")
    
    # Test serialization
    book_dict = book_summary.to_dict()
    book_from_dict = BookSummary.from_dict(book_dict)
    print(f"✅ Serialization works: {book_from_dict.book_title}")
    
    return book_summary


def test_config():
    """Test the configuration management."""
    print("\\n⚙️  Testing Configuration...")
    
    settings = Settings()
    print(f"✅ Settings loaded: {settings}")
    
    paths = settings.get_output_paths()
    print(f"✅ Output paths configured: {list(paths.keys())}")


def test_storage():
    """Test the storage management."""
    print("\\n💾 Testing Storage...")
    
    # Create test directory
    test_dir = Path("test_output")
    file_manager = FileManager(str(test_dir))
    print(f"✅ FileManager created with base dir: {test_dir}")
    
    # Test JSON serializer
    test_data = {"test": "data", "number": 42}
    json_str = JsonSerializer.to_json_string(test_data)
    parsed_data = JsonSerializer.from_json_string(json_str)
    print(f"✅ JSON serialization works: {parsed_data}")
    
    # Get storage stats
    stats = file_manager.get_storage_stats()
    print(f"✅ Storage stats: {stats}")
    
    # Clean up test directory
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print("✅ Test cleanup completed")


def main():
    """Run all tests."""
    print("🚀 Educational Content Processing - Module Test")
    print("=" * 60)
    
    try:
        # Test core functionality
        book_summary = test_models()
        test_config()
        test_storage()
        
        print("\\n🎉 All Tests Passed!")
        print("=" * 60)
        print("✅ Core models working correctly")
        print("✅ Configuration management ready")
        print("✅ Storage utilities functional")
        print("\\n💡 Next Steps:")
        print("   1. Extract content understanding logic")
        print("   2. Extract summarization logic")
        print("   3. Create pipeline orchestrator")
        print("   4. Add API endpoints")
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
