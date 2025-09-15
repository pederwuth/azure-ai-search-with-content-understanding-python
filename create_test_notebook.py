#!/usr/bin/env python3
"""
Quick script to create a manual testing notebook.
"""

notebook_content = '''
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Manual Content Understanding Testing\\n",
    "\\n",
    "This notebook allows you to manually test the Content Understanding pipeline with different PDFs and settings."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Import required libraries\\n",
    "import os\\n",
    "from pathlib import Path\\n",
    "from src.pipeline import process_pdf_with_content_understanding\\n",
    "\\n",
    "print(\\"Content Understanding Pipeline loaded successfully!\\")\\n",
    "\\n",
    "# List available PDFs\\n",
    "data_dir = Path(\\"data\\")\\n",
    "available_pdfs = list(data_dir.glob(\\"*.pdf\\")) if data_dir.exists() else []\\n",
    "\\n",
    "print(f\\"\\\\n📁 Available PDFs ({len(available_pdfs)}):\\")\\n",
    "for i, pdf in enumerate(available_pdfs, 1):\\n",
    "    print(f\\"   {i}. {pdf.name}\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Configuration - Modify these variables to test different combinations\\n",
    "\\n",
    "# Select PDF (change index to test different files)\\n",
    "PDF_INDEX = 0  # 0 = first PDF, 1 = second PDF, etc.\\n",
    "\\n",
    "# Analyzer template options\\n",
    "ANALYZER_TEMPLATE = \\"content_document\\"  # or \\"image_chart_diagram_understanding\\", etc.\\n",
    "\\n",
    "# Output settings\\n",
    "OUTPUT_DIR = \\"manual_notebook_test\\"\\n",
    "GENERATE_SUMMARY = True\\n",
    "\\n",
    "# Validate selection\\n",
    "if PDF_INDEX < len(available_pdfs):\\n",
    "    selected_pdf = available_pdfs[PDF_INDEX]\\n",
    "    print(f\\"✅ Selected PDF: {selected_pdf}\\")\\n",
    "    print(f\\"🔧 Analyzer Template: {ANALYZER_TEMPLATE}\\")\\n",
    "    print(f\\"📁 Output Directory: {OUTPUT_DIR}\\")\\n",
    "    print(f\\"📝 Generate Summary: {GENERATE_SUMMARY}\\")\\n",
    "else:\\n",
    "    print(f\\"❌ Invalid PDF_INDEX: {PDF_INDEX}. Available range: 0-{len(available_pdfs)-1}\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Process the selected PDF\\n",
    "\\n",
    "if PDF_INDEX < len(available_pdfs):\\n",
    "    print(f\\"🚀 Processing {selected_pdf.name}...\\")\\n",
    "    print(\\"=\\" * 50)\\n",
    "    \\n",
    "    try:\\n",
    "        result = process_pdf_with_content_understanding(\\n",
    "            pdf_path=str(selected_pdf),\\n",
    "            output_dir=OUTPUT_DIR,\\n",
    "            analyzer_template=ANALYZER_TEMPLATE,\\n",
    "            generate_summary=GENERATE_SUMMARY\\n",
    "        )\\n",
    "        \\n",
    "        print(\\"\\\\n✅ Processing completed successfully!\\")\\n",
    "        print(f\\"📊 Result keys: {list(result.keys())}\\")\\n",
    "        \\n",
    "        # Store result for inspection\\n",
    "        processing_result = result\\n",
    "        \\n",
    "    except Exception as e:\\n",
    "        print(f\\"❌ Processing failed: {e}\\")\\n",
    "        import traceback\\n",
    "        traceback.print_exc()\\n",
    "else:\\n",
    "    print(\\"❌ No valid PDF selected. Please update PDF_INDEX in the cell above.\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Inspect the results\\n",
    "\\n",
    "if \\'processing_result\\' in locals() and processing_result:\\n",
    "    print(\\"📈 Processing Results:\\")\\n",
    "    print(\\"=\\" * 30)\\n",
    "    \\n",
    "    for key, value in processing_result.items():\\n",
    "        if isinstance(value, str) and len(value) > 100:\\n",
    "            print(f\\"{key}: {value[:100]}...\\")\\n",
    "        else:\\n",
    "            print(f\\"{key}: {value}\\")\\n",
    "    \\n",
    "    # Show enhanced markdown content\\n",
    "    if \\'enhanced_markdown_content\\' in processing_result:\\n",
    "        print(\\"\\\\n📖 Enhanced Markdown Content:\\")\\n",
    "        print(\\"-\\" * 40)\\n",
    "        content = processing_result[\\'enhanced_markdown_content\\']\\n",
    "        print(f\\"Content length: {len(content)} characters\\")\\n",
    "        \\n",
    "        # Show first 1000 characters\\n",
    "        print(\\"\\\\nFirst 1000 characters:\\")\\n",
    "        print(content[:1000])\\n",
    "        \\n",
    "        if len(content) > 1000:\\n",
    "            print(\\"\\\\n... (truncated)\\")\\n",
    "else:\\n",
    "    print(\\"❌ No processing result available. Run the processing cell first.\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Check extracted figures\\n",
    "\\n",
    "if \\'processing_result\\' in locals() and \\'figures_directory\\' in processing_result:\\n",
    "    figures_dir = Path(processing_result[\\'figures_directory\\'])\\n",
    "    \\n",
    "    if figures_dir.exists():\\n",
    "        figures = list(figures_dir.glob(\\"*.png\\"))\\n",
    "        print(f\\"🖼️  Found {len(figures)} extracted figures:\\")\\n",
    "        \\n",
    "        for fig in figures:\\n",
    "            print(f\\"   - {fig.name} ({fig.stat().st_size} bytes)\\")\\n",
    "            \\n",
    "        if figures:\\n",
    "            print(\\"\\\\n💡 You can view these figure files in the output directory!\\")\\n",
    "    else:\\n",
    "        print(\\"❌ Figures directory not found\\")\\n",
    "else:\\n",
    "    print(\\"❌ No figures directory in result. Run the processing cell first.\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Quick comparison test - try different analyzer templates\\n",
    "\\n",
    "templates_to_test = [\\n",
    "    \\"content_document\\",\\n",
    "    \\"image_chart_diagram_understanding\\"\\n",
    "]\\n",
    "\\n",
    "print(\\"🧪 Quick Template Comparison Test\\")\\n",
    "print(\\"=\\" * 40)\\n",
    "\\n",
    "if PDF_INDEX < len(available_pdfs):\\n",
    "    for template in templates_to_test:\\n",
    "        print(f\\"\\\\n🔧 Testing template: {template}\\")\\n",
    "        try:\\n",
    "            result = process_pdf_with_content_understanding(\\n",
    "                pdf_path=str(available_pdfs[PDF_INDEX]),\\n",
    "                output_dir=f\\"comparison_test_{template}\\",\\n",
    "                analyzer_template=template,\\n",
    "                generate_summary=False  # Faster testing\\n",
    "            )\\n",
    "            \\n",
    "            content = result.get(\\'enhanced_markdown_content\\', \\'\\')\\n",
    "            print(f\\"   ✅ Success! Content length: {len(content)} chars\\")\\n",
    "            \\n",
    "            # Look for Content Understanding results\\n",
    "            if \\'FigureContent=\\' in content:\\n",
    "                import re\\n",
    "                matches = re.findall(r\\'FigureContent=\\\\\\"([^\\\\\\\\\"]*)\\\\\\"\\', content)\\n",
    "                print(f\\"   📊 Found {len(matches)} Content Understanding results\\")\\n",
    "                for i, match in enumerate(matches[:2]):  # Show first 2\\n",
    "                    preview = match[:50] + \\'...\\' if len(match) > 50 else match\\n",
    "                    print(f\\"      {i+1}. {preview}\\")\\n",
    "            \\n",
    "        except Exception as e:\\n",
    "            print(f\\"   ❌ Failed: {e}\\")\\n",
    "else:\\n",
    "    print(\\"❌ No valid PDF selected\\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
'''

with open('manual_testing.ipynb', 'w') as f:
    f.write(notebook_content)

print("📓 Created manual_testing.ipynb for interactive testing!")
print("💡 Open it in VS Code or Jupyter to run interactive tests.")
