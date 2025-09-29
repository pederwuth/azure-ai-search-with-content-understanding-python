"""
Document Processing Task

Wraps the enhanced document processing functionality as a pipeline task.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

from ..base import BaseTask
from ..models import TaskInputs, TaskOutputs, TaskMetadata, TaskInputType, TaskOutputType
from ...enhanced_document_processor import process_pdf_with_notebook_quality

logger = logging.getLogger(__name__)


class DocumentProcessingTask(BaseTask):
    """Task that processes PDF documents with enhanced content understanding"""

    @property
    def metadata(self) -> TaskMetadata:
        """Get task metadata"""
        return TaskMetadata(
            task_id="document_processing",
            name="Enhanced Document Processing",
            description="Process PDF documents with Azure Content Understanding to extract enhanced markdown, figures, and metadata",
            version="1.0.0",
            input_types=[TaskInputType.PDF],
            output_types=[
                TaskOutputType.ENHANCED_MARKDOWN,
                TaskOutputType.FIGURES,
                TaskOutputType.CACHE_FILE,
                TaskOutputType.METADATA
            ],
            dependencies=[],
            estimated_duration_minutes=15,
            resource_requirements={
                "azure_document_intelligence": True,
                "azure_content_understanding": True,
                "memory_gb": 2
            }
        )

    def validate_inputs(self, inputs: TaskInputs) -> bool:
        """
        Validate that inputs contain a PDF file for processing

        Args:
            inputs: Task inputs to validate

        Returns:
            bool: True if inputs contain a PDF file
        """
        # Check for PDF file in files or data
        has_pdf = (
            'pdf' in inputs.files or
            'file' in inputs.files or
            'pdf_content' in inputs.data
        )

        if not has_pdf:
            self.logger.error(
                "No PDF file found in inputs for document processing")
            self.logger.error(f"Available files: {list(inputs.files.keys())}")
            self.logger.error(f"Available data: {list(inputs.data.keys())}")

        return has_pdf

    async def execute(self, inputs: TaskInputs) -> TaskOutputs:
        """
        Execute document processing

        Args:
            inputs: Task inputs containing PDF file

        Returns:
            TaskOutputs: Processing results including enhanced markdown and figures
        """
        self.logger.info("Starting enhanced document processing")

        # Get PDF file from inputs
        pdf_file = None
        if 'pdf' in inputs.files:
            pdf_file = inputs.files['pdf']
        elif 'pdf_file' in inputs.files:
            pdf_file = inputs.files['pdf_file']
        elif 'pdf' in inputs.data:
            # Handle case where PDF is passed as bytes
            pdf_data = inputs.data['pdf']
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix='.pdf')
            temp_file.write(pdf_data)
            temp_file.close()
            pdf_file = Path(temp_file.name)

        if pdf_file is None or not pdf_file.exists():
            raise ValueError("No valid PDF file found in inputs")

        self.logger.info(f"Processing PDF: {pdf_file}")

        # Debug: Log all input data keys and values
        self.logger.info(
            f"🔍 Document task inputs.data keys: {list(inputs.data.keys())}")
        self.logger.info(
            f"🔍 Document task custom_filename: {inputs.data.get('custom_filename')}")
        self.logger.info(
            f"🔍 Document task original_filename: {inputs.data.get('original_filename')}")

        # Get configuration from inputs
        custom_filename = inputs.data.get('custom_filename')
        analyzer_template = inputs.data.get(
            'analyzer_template',
            'analyzer_templates/image_chart_diagram_understanding.json'
        )
        use_content_books_structure = inputs.data.get(
            'use_content_books_structure', True)
        content_type = inputs.data.get('content_type', 'book')
        original_filename = inputs.data.get('original_filename', pdf_file.name)

        # Determine output directory
        output_dir = inputs.data.get('output_dir', 'content/books')

        try:
            # Process the document
            results = process_pdf_with_notebook_quality(
                pdf_path=pdf_file,
                output_dir=output_dir,
                analyzer_template_path=analyzer_template,
                custom_filename=custom_filename,
                use_content_books_structure=use_content_books_structure,
                content_type=content_type,
                original_filename=original_filename
            )

            self.logger.info("Document processing completed successfully")

            # Prepare outputs
            outputs = TaskOutputs()

            # Add file outputs
            if 'enhanced_markdown' in results:
                outputs.add_file('enhanced_markdown',
                                 results['enhanced_markdown'])

            if 'cache_file' in results:
                outputs.add_file('cache_file', results['cache_file'])

            if 'figures_directory' in results:
                # Add figures directory as data, not as file since it's a directory
                outputs.add_data('figures_directory', str(
                    results['figures_directory']))

            if 'metadata_file' in results:
                outputs.add_file('metadata', results['metadata_file'])

            # Add data outputs
            outputs.add_data('processing_stats',
                             results.get('processing_stats', {}))
            outputs.add_data('figures_processed',
                             results.get('figures_processed', 0))
            outputs.add_data('document_length',
                             results.get('document_length', 0))
            outputs.add_data('book_title', results.get('book_title'))
            outputs.add_data('main_folder', results.get('main_folder'))

            # Add all results as metadata
            outputs.metadata.update(results)

            return outputs

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup after task execution"""
        # Clean up any temporary files if needed
        pass
