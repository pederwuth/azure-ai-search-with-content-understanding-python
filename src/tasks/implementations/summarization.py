"""
Summarization Task

Wraps the book summarization functionality as a pipeline task.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from ..base import BaseTask
from ..models import TaskInputs, TaskOutputs, TaskMetadata, TaskInputType, TaskOutputType
from ...summarization.factory import get_summarization_factory

logger = logging.getLogger(__name__)


class SummarizationTask(BaseTask):
    """Task that summarizes markdown content into structured book summaries"""

    @property
    def metadata(self) -> TaskMetadata:
        """Get task metadata"""
        return TaskMetadata(
            task_id="summarization",
            name="Book Summarization",
            description="Generate comprehensive book summaries with chapter analysis, key themes, and learning objectives",
            version="1.0.0",
            input_types=[TaskInputType.MARKDOWN,
                         TaskInputType.ENHANCED_MARKDOWN],
            output_types=[TaskOutputType.BOOK_SUMMARY,
                          TaskOutputType.METADATA],
            dependencies=["document_processing"],
            estimated_duration_minutes=10,
            resource_requirements={
                "azure_openai": True,
                "memory_gb": 1
            }
        )

    def validate_inputs(self, inputs: TaskInputs) -> bool:
        """
        Validate that inputs contain markdown content for summarization

        Args:
            inputs: Task inputs to validate

        Returns:
            bool: True if inputs contain markdown content
        """
        # Check for enhanced_markdown or markdown in files or data
        has_markdown = (
            'enhanced_markdown' in inputs.files or
            'markdown' in inputs.files or
            'enhanced_markdown' in inputs.data or
            'markdown' in inputs.data
        )

        if not has_markdown:
            self.logger.error(
                "No markdown content found in inputs for summarization")
            self.logger.error(f"Available files: {list(inputs.files.keys())}")
            self.logger.error(f"Available data: {list(inputs.data.keys())}")

        return has_markdown

    async def execute(self, inputs: TaskInputs) -> TaskOutputs:
        """
        Execute book summarization

        Args:
            inputs: Task inputs containing markdown content

        Returns:
            TaskOutputs: Summarization results including book summary and metadata
        """
        self.logger.info("Starting book summarization")

        # Get markdown content from inputs
        markdown_content = None
        book_title = inputs.data.get('book_title', 'Unknown Book')

        # Try to get markdown from various sources
        if 'enhanced_markdown' in inputs.files:
            markdown_file = inputs.files['enhanced_markdown']
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            self.logger.info(
                f"Using enhanced markdown from file: {markdown_file}")

        elif 'markdown' in inputs.files:
            markdown_file = inputs.files['markdown']
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            self.logger.info(f"Using markdown from file: {markdown_file}")

        elif 'enhanced_markdown' in inputs.data:
            markdown_content = inputs.data['enhanced_markdown']
            self.logger.info("Using enhanced markdown from data")

        elif 'markdown' in inputs.data:
            markdown_content = inputs.data['markdown']
            self.logger.info("Using markdown from data")

        if not markdown_content:
            raise ValueError("No markdown content found in inputs")

        # Extract book title from available sources
        if 'book_title' in inputs.data:
            book_title = inputs.data['book_title']
        elif 'title' in inputs.data:
            book_title = inputs.data['title']
        elif hasattr(inputs, 'metadata') and 'book_title' in inputs.metadata:
            book_title = inputs.metadata['book_title']

        self.logger.info(f"Summarizing book: {book_title}")

        try:
            # Get summarization factory and process
            factory = get_summarization_factory()
            book_summary = await factory.summarize_markdown_async(markdown_content, book_title)

            self.logger.info("Book summarization completed successfully")
            self.logger.info(
                f"Generated summary for {book_summary.total_chapters} chapters")

            # Prepare outputs
            outputs = TaskOutputs()

            # Add the book summary as data (convert to dict for JSON serialization)
            book_summary_dict = {
                'book_title': book_summary.book_title,
                'overall_summary': book_summary.overall_summary,
                'key_themes': book_summary.key_themes,
                'learning_objectives': book_summary.learning_objectives,
                'chapter_summaries': [
                    {
                        'chapter_number': ch.chapter_number,
                        'chapter_title': ch.chapter_title,
                        'summary': ch.summary,
                        'key_concepts': ch.key_concepts,
                        'main_topics': ch.main_topics,
                        'token_count': ch.token_count,
                        'created_at': ch.created_at.isoformat() if ch.created_at else None
                    } for ch in book_summary.chapter_summaries
                ],
                'total_chapters': book_summary.total_chapters,
                'created_at': book_summary.created_at.isoformat() if book_summary.created_at else None
            }

            # Save book summary to file
            import json
            from pathlib import Path

            # Get the output directory from inputs (passed from document processing)
            output_dir = inputs.data.get('main_folder')
            self.logger.info(
                f"🔍 Summary file save - output_dir from inputs: {output_dir}")
            self.logger.info(
                f"🔍 Summary file save - inputs.data keys: {list(inputs.data.keys())}")

            if output_dir:
                # Convert to absolute path if relative
                from pathlib import Path
                import os
                import re

                self.logger.info(
                    f"🔍 Summary file save - original output_dir: {output_dir}")

                if not Path(output_dir).is_absolute():
                    output_dir = os.path.join(os.getcwd(), output_dir)
                    self.logger.info(
                        f"🔍 Summary file save - converted to absolute path: {output_dir}")

                output_path = Path(output_dir)
                summary_dir = output_path / "processed"

                # Extract components from folder name: {book_name}-book-{timestamp}-{job_id}
                folder_name = output_path.stem
                match = re.match(
                    r'^(.+)-book-(\d{8}_\d{6})-([a-f0-9\-]{36}|[a-f0-9]{8})$', folder_name)

                if match:
                    book_name, timestamp, job_id = match.groups()
                    summary_filename = f"{book_name}-summary-{timestamp}-{job_id}.json"
                else:
                    # Fallback to original naming if pattern doesn't match
                    self.logger.warning(
                        f"⚠️ Could not parse folder name pattern: {folder_name}, using fallback naming")
                    summary_filename = f"{folder_name}-summary.json"

                summary_file = summary_dir / summary_filename

                self.logger.info(
                    f"🔍 Summary file save - summary_dir: {summary_dir}")
                self.logger.info(
                    f"🔍 Summary file save - summary_file: {summary_file}")

                # Ensure directory exists
                summary_dir.mkdir(parents=True, exist_ok=True)

                try:
                    # Save summary as JSON file
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        json.dump(book_summary_dict, f,
                                  indent=2, ensure_ascii=False)

                    # Add summary file to outputs
                    outputs.add_file('book_summary_file', summary_file)
                    self.logger.info(
                        f"✅ Book summary saved successfully to: {summary_file}")
                except Exception as e:
                    self.logger.error(f"❌ ERROR saving summary file: {e}")
                    import traceback
                    self.logger.error(
                        f"❌ Full traceback: {traceback.format_exc()}")
            else:
                self.logger.warning(
                    "⚠️ No main_folder found in inputs, skipping file save")

            outputs.add_data('book_summary', book_summary_dict)

            # Add summary components as separate data fields for easy access
            outputs.add_data('book_title', book_summary.book_title)
            outputs.add_data('overall_summary', book_summary.overall_summary)
            outputs.add_data('key_themes', book_summary.key_themes)
            outputs.add_data('learning_objectives',
                             book_summary.learning_objectives)
            # Use serialized version
            outputs.add_data('chapter_summaries',
                             book_summary_dict['chapter_summaries'])
            outputs.add_data('total_chapters', book_summary.total_chapters)

            # Add processing metadata
            outputs.metadata.update({
                'summarization_completed': True,
                'total_chapters': book_summary.total_chapters,
                'key_themes_count': len(book_summary.key_themes),
                'learning_objectives_count': len(book_summary.learning_objectives),
                'created_at': book_summary.created_at.isoformat() if book_summary.created_at else None
            })

            return outputs

        except Exception as e:
            self.logger.error(f"Book summarization failed: {e}")
            raise

    def can_process(self, available_outputs: Dict[str, Any]) -> bool:
        """
        Check if this task can run with available outputs

        Args:
            available_outputs: Outputs available from previous tasks

        Returns:
            bool: True if task can run with available outputs
        """
        # Can process if we have any markdown content
        return (
            'markdown' in available_outputs or
            'enhanced_markdown' in available_outputs or
            any(key.endswith('markdown') for key in available_outputs)
        )
