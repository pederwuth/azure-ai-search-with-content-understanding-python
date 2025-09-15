#!/usr/bin/env python3
"""
Debug script to isolate the file I/O issue.
"""

import os
import tempfile
from pathlib import Path

def test_file_operations():
    """Test basic file operations to identify the I/O issue."""
    
    # Test 1: Basic file creation and reading
    print("🔍 Testing basic file operations...")
    
    test_pdf = "data/sample_layout.pdf"
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    print(f"✅ Test PDF found: {test_pdf}")
    
    # Test 2: Create temporary file like in API server
    print("\n🔍 Testing temporary file creation...")
    
    try:
        with open(test_pdf, 'rb') as source:
            content = source.read()
            print(f"✅ Read {len(content)} bytes from source PDF")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_pdf_path = temp_file.name
            print(f"✅ Created temporary file: {temp_pdf_path}")
        
        # Test 3: Verify temp file is readable
        with open(temp_pdf_path, 'rb') as temp_read:
            temp_content = temp_read.read()
            print(f"✅ Read {len(temp_content)} bytes from temp file")
            print(f"✅ Content matches: {len(content) == len(temp_content)}")
        
        # Test 4: Test our pipeline imports
        print("\n🔍 Testing pipeline imports...")
        try:
            from src.pipeline import ContentUnderstandingPipeline, process_pdf_with_content_understanding
            print("✅ Pipeline imports successful")
            
            # Test 5: Initialize pipeline
            print("\n🔍 Testing pipeline initialization...")
            pipeline = ContentUnderstandingPipeline()
            print("✅ Pipeline initialized successfully")
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return False
        
        # Clean up
        os.unlink(temp_pdf_path)
        print("✅ Temporary file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ File operation error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Debugging File I/O Issue")
    print("=" * 50)
    
    success = test_file_operations()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All file operations successful")
        print("💡 The I/O issue may be in the pipeline processing")
    else:
        print("❌ File operation issue identified")
