#!/usr/bin/env python3
"""
Test script for the new content/books folder structure implementation.
"""

import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from enhanced_document_processor import process_pdf_with_notebook_quality

def test_new_folder_structure():
    """Test the new content/books folder structure with sample_layout.pdf"""
    
    # Test parameters
    pdf_path = "data/sample_layout.pdf"
    output_dir = "content/books"
    custom_filename = "sample_layout_test"
    
    print("🧪 Testing new content/books folder structure...")
    print(f"📄 Input PDF: {pdf_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📝 Custom filename: {custom_filename}")
    print()
    
    try:
        # Process with new structure
        results = process_pdf_with_notebook_quality(
            pdf_path=pdf_path,
            output_dir=output_dir,
            custom_filename=custom_filename,
            use_content_books_structure=True,
            content_type="book"
        )
        
        print("✅ Processing completed successfully!")
        print()
        print("📊 Results:")
        print(f"   Main folder: {results.get('main_folder', 'N/A')}")
        print(f"   Book title: {results.get('book_title', 'N/A')}")
        print(f"   Job ID: {results.get('job_id', 'N/A')}")
        print(f"   Timestamp: {results.get('timestamp', 'N/A')}")
        print(f"   Content type: {results.get('content_type', 'N/A')}")
        print(f"   Folder structure: {results.get('folder_structure', 'N/A')}")
        print()
        print(f"   Enhanced markdown: {results.get('enhanced_markdown', 'N/A')}")
        print(f"   Cache file: {results.get('cache_file', 'N/A')}")
        print(f"   Figures directory: {results.get('figures_directory', 'N/A')}")
        print(f"   Metadata file: {results.get('metadata_file', 'N/A')}")
        print()
        print(f"   Figures processed: {results.get('figures_processed', 0)}")
        print(f"   Document length: {results.get('document_length', 0):,} characters")
        
        # Verify folder structure exists
        main_folder = Path(results.get('main_folder', ''))
        if main_folder.exists():
            print()
            print("📁 Folder structure verification:")
            print(f"   ✅ Main folder exists: {main_folder}")
            
            # Check subdirectories
            input_dir = main_folder / "input"
            processed_dir = main_folder / "processed"
            
            print(f"   ✅ Input directory: {input_dir.exists()}")
            print(f"   ✅ Processed directory: {processed_dir.exists()}")
            
            # Check for markdown and figures directories
            for item in processed_dir.iterdir():
                if item.is_dir() and "markdown" in item.name:
                    print(f"   ✅ Markdown directory: {item}")
                    figures_dir = list(item.glob("*figures*"))
                    if figures_dir:
                        print(f"   ✅ Figures directory: {figures_dir[0]}")
            
            # Check metadata file
            metadata_file = main_folder / "metadata.json"
            print(f"   ✅ Metadata file: {metadata_file.exists()}")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_folder_structure()