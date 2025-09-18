#!/usr/bin/env python3
"""
Test script for the enhanced document processor with the valueArray fix.
"""

from src.enhanced_document_processor import EnhancedDocumentProcessor
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_enhanced_processing():
    """Test the enhanced document processing with a sample PDF."""

    print("🧪 Testing Enhanced Document Processing...")

    # Initialize the processor
    processor = EnhancedDocumentProcessor()

    # Use a sample PDF from the data directory
    sample_pdf = "data/sample_layout.pdf"

    if not os.path.exists(sample_pdf):
        print(f"❌ Sample PDF not found: {sample_pdf}")
        return False

    print(f"📄 Processing: {sample_pdf}")

    try:
        # Test the enhanced processing
        result = await processor.process_document_enhanced(
            pdf_path=sample_pdf,
            custom_filename="test_sample_layout"
        )

        print("✅ Processing completed successfully!")
        print(f"📊 Results:")
        print(
            f"   - Document length: {result['document_length']:,} characters")
        print(
            f"   - Figures processed: {result['processing_stats']['figures_processed']}")
        print(
            f"   - Estimated tokens: {result['processing_stats']['estimated_tokens']:,}")
        print(f"   - Enhanced markdown: {result['enhanced_markdown_path']}")

        return True

    except Exception as e:
        print(f"❌ Processing failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_enhanced_processing())

    if success:
        print("\n🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test failed!")
        sys.exit(1)
