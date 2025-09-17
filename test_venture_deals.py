#!/usr/bin/env python3
import os
import sys
import asyncio
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
        result_dict = process_pdf_with_notebook_quality('data/Venture-deals.pdf')
        
        # Get the markdown content
        result = result_dict.get('markdown_content', '')
        
        print('✅ Enhanced processing completed successfully!')
        print(f'📊 Output length: {len(result):,} characters')
        print(f'🧮 Estimated tokens: ~{len(result)//5:,}')
        
        # Save to output file
        output_dir = Path('test_output/venture_deals_enhanced')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / 'venture_deals_enhanced.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f'📄 Output saved to {output_file}')
        print()
        
        # Show some stats about the content
        lines = result.split('\n')
        print("📈 Content Analysis:")
        print(f"   • Total lines: {len(lines):,}")
        print(f"   • Non-empty lines: {len([l for l in lines if l.strip()]):,}")
        
        # Count figures
        figure_count = result.count('![Figure')
        print(f"   • Figures detected: {figure_count}")
        
        # Count tables
        table_count = result.count('|')
        print(f"   • Table elements: {table_count}")
        
        # Show first few lines
        print("\n📋 First few lines of output:")
        for i, line in enumerate(lines[:10]):
            if line.strip():
                print(f"   {i+1:2d}: {line[:100]}{'...' if len(line) > 100 else ''}")
        
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