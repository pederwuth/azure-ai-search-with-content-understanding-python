#!/usr/bin/env python3
"""
Test script to debug summary file saving
"""

import logging
import json
from pathlib import Path
from src.tasks.implementations.summarization import SummarizationTask
from src.tasks.models import TaskInputs

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create test inputs
test_data = {
    'main_folder': 'content/books/test-summary-save',
    'enhanced_markdown': 'This is test content for summarization',
    'book_title': 'Test Book'
}

inputs = TaskInputs(data=test_data)

# Create summarization task
task = SummarizationTask()

print("Testing summary file save...")
print(f"Test data: {test_data}")

# Create the test directory
test_dir = Path(test_data['main_folder'])
test_dir.mkdir(parents=True, exist_ok=True)

# Try to run the file save logic directly
try:
    # Get the output directory from inputs (passed from document processing)
    output_dir = inputs.data.get('main_folder')
    print(f"🔍 output_dir from inputs: {output_dir}")
    print(f"🔍 inputs.data keys: {list(inputs.data.keys())}")

    if output_dir:
        # Convert to absolute path if relative
        import os

        print(f"🔍 original output_dir: {output_dir}")

        if not Path(output_dir).is_absolute():
            output_dir = os.path.join(os.getcwd(), output_dir)
            print(f"🔍 converted to absolute path: {output_dir}")

        output_path = Path(output_dir)
        summary_dir = output_path / "processed"
        summary_file = summary_dir / f"{output_path.stem}-summary.json"

        print(f"🔍 summary_dir: {summary_dir}")
        print(f"🔍 summary_file: {summary_file}")

        # Ensure directory exists
        summary_dir.mkdir(parents=True, exist_ok=True)

        # Create test summary data
        test_summary = {
            "book_title": "Test Book",
            "overall_summary": "This is a test summary",
            "key_themes": ["Testing", "Debugging"],
            "chapter_summaries": []
        }

        # Save summary as JSON file
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, indent=2, ensure_ascii=False)

        print(f"✅ Test summary saved successfully to: {summary_file}")

        # Verify file exists
        if summary_file.exists():
            print(f"✅ File verified to exist: {summary_file}")
            print(f"File size: {summary_file.stat().st_size} bytes")
        else:
            print(f"❌ File does not exist after save: {summary_file}")

    else:
        print("⚠️ No main_folder found in inputs")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
