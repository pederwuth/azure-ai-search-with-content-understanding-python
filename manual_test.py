#!/usr/bin/env python3
"""
Manual test script for Content Understanding pipeline.
"""

import os
from pathlib import Path

def test_content_extraction_manual():
    """Test content extraction manually with different PDFs."""
    
    # Import the pipeline
    from src.pipeline import process_pdf_with_content_understanding
    
    # Available test PDFs
    test_pdfs = [
        "data/sample_layout.pdf",
        "data/sample_report.pdf", 
        "data/Venture-deals.pdf"
    ]
    
    print("🧪 Manual Content Extraction Testing")
    print("=" * 50)
    
    # List available PDFs
    print("📁 Available test PDFs:")
    for i, pdf in enumerate(test_pdfs, 1):
        if os.path.exists(pdf):
            print(f"   {i}. {pdf} ✅")
        else:
            print(f"   {i}. {pdf} ❌ (not found)")
    
    print("\n🔧 Available analyzer templates:")
    templates_dir = Path("analyzer_templates")
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.json"):
            print(f"   - {template_file.stem}")
    
    print("\n" + "=" * 50)
    
    # Interactive selection
    while True:
        try:
            pdf_choice = input("\n📄 Select PDF (1-3) or 'q' to quit: ").strip()
            
            if pdf_choice.lower() == 'q':
                print("👋 Goodbye!")
                break
                
            pdf_index = int(pdf_choice) - 1
            if 0 <= pdf_index < len(test_pdfs):
                selected_pdf = test_pdfs[pdf_index]
                
                if not os.path.exists(selected_pdf):
                    print(f"❌ PDF not found: {selected_pdf}")
                    continue
                
                # Get analyzer template
                template = input("🔧 Analyzer template (default: content_document): ").strip()
                if not template:
                    template = "content_document"
                
                # Get output directory
                output_dir = input("📁 Output directory (default: manual_test_output): ").strip()
                if not output_dir:
                    output_dir = "manual_test_output"
                
                print(f"\n🚀 Processing {selected_pdf}...")
                print(f"   Template: {template}")
                print(f"   Output: {output_dir}")
                print("-" * 30)
                
                try:
                    # Process the PDF
                    result = process_pdf_with_content_understanding(
                        pdf_path=selected_pdf,
                        output_dir=output_dir,
                        analyzer_template=template,
                        generate_summary=True
                    )
                    
                    print("\n✅ Processing completed!")
                    print(f"📊 Result keys: {list(result.keys())}")
                    
                    # Show results
                    if 'enhanced_markdown_path' in result:
                        print(f"📝 Enhanced markdown: {result['enhanced_markdown_path']}")
                        
                        # Show preview
                        with open(result['enhanced_markdown_path'], 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"\n📖 Content preview ({len(content)} chars):")
                            print("-" * 40)
                            print(content[:500] + "..." if len(content) > 500 else content)
                    
                    if 'figures_directory' in result:
                        figures_dir = Path(result['figures_directory'])
                        if figures_dir.exists():
                            figures = list(figures_dir.glob("*.png"))
                            print(f"\n🖼️  Extracted {len(figures)} figures:")
                            for fig in figures:
                                print(f"   - {fig.name}")
                    
                except Exception as e:
                    print(f"❌ Processing failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Invalid selection. Please choose 1-3.")
                
        except ValueError:
            print("❌ Please enter a number (1-3) or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    test_content_extraction_manual()
