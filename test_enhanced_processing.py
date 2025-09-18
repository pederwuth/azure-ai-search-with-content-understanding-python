#!/usr/bin/env python3
"""
Test the enhanced document processor directly to verify the fixes work.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from enhanced_document_processor import EnhancedDocumentProcessor

def test_enhanced_processing():
    """Test enhanced processing with a sample PDF."""
    
    # Initialize the processor
    processor = EnhancedDocumentProcessor()
    
    # Test with the sample layout PDF
    pdf_path = "data/sample_layout.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        print("Available files in data/:")
        for f in Path("data").glob("*.pdf"):
            print(f"  - {f}")
        return False
    
    try:
        print(f"🧪 Testing enhanced processing with: {pdf_path}")
        
        # Process the document
        result = processor.process_document(
            pdf_path=pdf_path,
            output_dir="test_output",
            custom_filename="test_document"
        )
        
        print("✅ Processing completed successfully!")
        print(f"📊 Results summary:")
        print(f"   - Document length: {result.get('document_length', 'Unknown'):,} characters")
        print(f"   - Figures processed: {result.get('figures_processed', 'Unknown')}")
        print(f"   - Processing time: {result.get('processing_stats', {}).get('total_time', 'Unknown')} seconds")
        
        # Check if markdown file was created
        markdown_files = list(Path("test_output").glob("**/*.md"))
        if markdown_files:
            print(f"📝 Markdown files created: {len(markdown_files)}")
            for md_file in markdown_files[:3]:  # Show first 3
                print(f"   - {md_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_processing()
    sys.exit(0 if success else 1)