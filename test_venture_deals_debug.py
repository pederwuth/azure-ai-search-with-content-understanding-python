#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append('src')
from enhanced_document_processor import process_pdf_with_notebook_quality

def test_venture_deals():
    """Test enhanced document processor with Venture-deals.pdf"""
    print("🚀 Testing Enhanced Document Processor with Venture-deals.pdf")
    print("-" * 60)
    
    try:
        # Process the large PDF file
        print("📖 Processing Venture-deals.pdf...")
        result_dict = process_pdf_with_notebook_quality(
            'data/Venture-deals.pdf',
            output_dir='test_output/venture_deals_enhanced'
        )
        
        print('✅ Enhanced processing completed successfully!')
        print(f"📊 Result type: {type(result_dict)}")
        print(f"📊 Result keys: {list(result_dict.keys()) if isinstance(result_dict, dict) else 'Not a dict'}")
        
        # Check if there are output files
        output_dir = Path('test_output/venture_deals_enhanced')
        if output_dir.exists():
            files = list(output_dir.glob('*'))
            print(f"📁 Output files created: {len(files)}")
            for file in files:
                print(f"   • {file.name} ({file.stat().st_size:,} bytes)")
                
                # If it's a markdown file, show some content
                if file.suffix == '.md':
                    content = file.read_text(encoding='utf-8')
                    print(f"   📄 Content length: {len(content):,} characters")
                    
                    if content:
                        lines = content.split('\n')
                        print(f"   📄 Lines: {len(lines):,}")
                        print(f"   📄 Non-empty lines: {len([l for l in lines if l.strip()]):,}")
                        
                        # Show first few lines
                        print("   📋 First few lines:")
                        for i, line in enumerate(lines[:5]):
                            if line.strip():
                                print(f"      {i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_venture_deals()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)