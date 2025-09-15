#!/usr/bin/env python3
"""
Debug script to test the actual pipeline processing.
"""

import os
import tempfile
from pathlib import Path

def test_pipeline_processing():
    """Test the actual pipeline processing to find the I/O issue."""
    
    print("🔍 Testing pipeline processing...")
    
    test_pdf = "data/sample_layout.pdf"
    
    try:
        # Create temp file like API server does
        with open(test_pdf, 'rb') as source:
            content = source.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_pdf_path = temp_file.name
        
        print(f"✅ Temporary file created: {temp_pdf_path}")
        
        # Test the convenience function
        from src.pipeline import process_pdf_with_content_understanding
        
        print("🔍 Testing process_pdf_with_content_understanding...")
        
        result = process_pdf_with_content_understanding(
            pdf_path=temp_pdf_path,
            output_dir="test_output",
            analyzer_template="content_document",
            generate_summary=True
        )
        
        print("✅ Pipeline processing completed successfully!")
        print(f"📊 Result keys: {list(result.keys())}")
        
        # Clean up
        os.unlink(temp_pdf_path)
        print("✅ Temporary file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline processing error: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
        
        return False

if __name__ == "__main__":
    print("🧪 Testing Pipeline Processing")
    print("=" * 50)
    
    success = test_pipeline_processing()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Pipeline processing works!")
        print("💡 The issue might be in the API server's async handling")
    else:
        print("❌ Pipeline processing issue identified")
