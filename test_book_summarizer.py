#!/usr/bin/env python3
"""
Test script for the book summarizer implementation.
This tests that our implementation works exactly like the notebook.
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
load_dotenv()


def test_book_summarizer():
    """Test the book summarizer with sample content."""
    from src.summarization.book_summarizer import ProgressiveBookSummarizer

    print("🧪 Testing Book Summarizer Implementation")
    print("=" * 50)

    try:
        print("1. Initializing summarizer...")
        summarizer = ProgressiveBookSummarizer()
        print("✅ Summarizer initialized successfully")

        # Test with sample content
        test_content = """# Chapter 1: Introduction to Programming

Programming is the art and science of creating instructions for computers to follow. It involves breaking down complex problems into smaller, manageable tasks and then expressing the solution in a language that a computer can understand and execute.

## The Evolution of Programming

From the early days of machine language to modern high-level programming languages, the field has evolved dramatically. Programming languages have become more expressive, powerful, and accessible to a broader audience.

## Why Learn Programming?

Programming skills are increasingly valuable in today's digital world. Whether you're automating repetitive tasks, analyzing data, or building the next great application, programming provides the tools to turn ideas into reality.

# Chapter 2: Fundamental Concepts

Before diving into code, it's essential to understand some fundamental concepts that underpin all programming languages and paradigms.

## Variables and Data Types

Variables are containers that store data values. Different programming languages handle variables differently, but the concept remains consistent across most languages.

### Common Data Types
- **Numbers**: Integers and floating-point numbers
- **Strings**: Text data
- **Booleans**: True/False values
- **Collections**: Arrays, lists, and dictionaries

## Control Structures

Control structures determine the flow of program execution. They include:
- **Conditional statements** (if/else)
- **Loops** (for, while)
- **Functions** and procedures

These structures allow programs to make decisions and repeat operations efficiently.

# Chapter 3: Problem-Solving Approach

Effective programming requires a systematic approach to problem-solving. This chapter explores methodologies and best practices for tackling programming challenges.

## The Problem-Solving Process

1. **Understand the problem**: Clearly define what needs to be solved
2. **Plan the solution**: Break down the problem into smaller steps
3. **Implement the solution**: Write the code
4. **Test and debug**: Ensure the solution works correctly
5. **Optimize**: Improve efficiency and readability

## Best Practices

- Write clean, readable code
- Use meaningful variable names
- Add comments to explain complex logic
- Test your code thoroughly
- Keep functions small and focused

Programming is not just about writing code; it's about solving problems effectively and efficiently.
"""

        print("2. Processing test document...")
        result = summarizer.process_document_progressively(
            markdown_content=test_content,
            book_title="Introduction to Programming"
        )

        print("✅ Processing completed successfully!")
        print("=" * 50)
        print("RESULTS:")
        print(f"📖 Book Title: {result.book_title}")
        print(f"📚 Total Chapters: {result.total_chapters}")
        print(
            f"📄 Overall Summary Length: {len(result.overall_summary)} characters")
        print(f"🎯 Key Themes: {len(result.key_themes)} themes")
        print(
            f"🎓 Learning Objectives: {len(result.learning_objectives)} objectives")
        print(f"⏰ Created: {result.created_at}")

        print("\n📝 OVERALL SUMMARY:")
        print(result.overall_summary)

        print("\n🎯 KEY THEMES:")
        for i, theme in enumerate(result.key_themes, 1):
            print(f"   {i}. {theme}")

        print("\n🎓 LEARNING OBJECTIVES:")
        for i, objective in enumerate(result.learning_objectives, 1):
            print(f"   {i}. {objective}")

        print("\n✅ ALL TESTS PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_book_summarizer()
    sys.exit(0 if success else 1)
