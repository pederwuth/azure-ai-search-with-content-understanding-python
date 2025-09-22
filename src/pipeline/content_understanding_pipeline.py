"""
Content Understanding pipeline for educational content processing.

This module provides a high-level pipeline that combines Document Intelligence,
Content Understanding, and summarization capabilities for comprehensive
educational content processing.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from azure.identity import DefaultAzureCredential

from ..core.models import BookChapter, BookSummary
from ..core.config import Settings
from ..core.exceptions import PipelineError
from ..storage.file_manager import FileManager
from ..content_understanding.document_processor import DocumentProcessor

# Import summarization factory for flexible summarization
from ..summarization.factory import get_summarization_factory

logger = logging.getLogger(__name__)


class ContentUnderstandingPipeline:
    """Pipeline for processing educational content with Azure AI services."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the pipeline.

        Args:
            settings: Application settings. If None, will load from environment.
        """
        self.settings = settings or Settings()
        self.credential = DefaultAzureCredential()

        # Initialize components
        self.file_manager = FileManager()
        
        # Initialize summarization factory (handles service/direct mode automatically)
        self.summarization_factory = get_summarization_factory()

        self.document_processor = DocumentProcessor(
            self.settings, self.credential)

        logger.info("Content Understanding pipeline initialized")

    def process_pdf_with_understanding(
        self,
        pdf_path: str,
        output_dir: str = "output",
        analyzer_template: str = "content_document",
        figures_dir: Optional[str] = None,
        generate_summary: bool = True,
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process PDF with content understanding and optional summarization.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output files
            analyzer_template: Content Understanding analyzer template name
            figures_dir: Directory for extracted figures (defaults to {output_dir}/figures)
            generate_summary: Whether to generate a book summary
            custom_filename: Custom filename for the enhanced markdown (without extension)

        Returns:
            Dictionary containing processing results

        Raises:
            PipelineError: If pipeline processing fails
        """
        try:
            logger.info(f"Starting PDF processing pipeline for: {pdf_path}")

            # Validate inputs
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise PipelineError(f"PDF file not found: {pdf_path}")

            # Set up directories
            output_path = Path(output_dir).resolve()  # Use absolute path
            output_path.mkdir(parents=True, exist_ok=True)

            if figures_dir is None:
                figures_dir = str(output_path / "figures")

            # Get analyzer template path
            analyzer_template_path = self._get_analyzer_template_path(
                analyzer_template)

            # Process PDF to enhanced markdown
            logger.info(
                "Processing PDF with Document Intelligence and Content Understanding")
            enhanced_markdown = self.document_processor.process_pdf_to_markdown(
                pdf_path=pdf_path,
                analyzer_template_path=analyzer_template_path,
                output_figures_dir=figures_dir
            )

            # Determine the filename for the enhanced markdown
            if custom_filename:
                # Use custom filename provided by caller
                base_name = custom_filename
                # Save to processed subdirectory if custom filename includes a path
                if '/' in custom_filename:
                    markdown_file = output_path / custom_filename
                else:
                    # Create processed subdirectory and save there
                    processed_dir = output_path / "processed"
                    processed_dir.mkdir(exist_ok=True)
                    markdown_file = processed_dir / \
                        f"{custom_filename}_enhanced.md"
            else:
                # Use original logic for backward compatibility
                original_filename = getattr(
                    pdf_file, '_original_name', pdf_file.name)
                if original_filename.startswith('tmp') and '.' in original_filename:
                    # This is a temporary file, try to get original name from context
                    base_name = "document"  # fallback name
                else:
                    base_name = Path(original_filename).stem

                markdown_file = output_path / f"{base_name}_enhanced.md"

            # Save the enhanced markdown
            markdown_file.parent.mkdir(parents=True, exist_ok=True)
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_markdown)

            logger.info(f"Enhanced markdown saved to: {markdown_file}")

            results = {
                "pdf_path": pdf_path,
                "enhanced_markdown_path": str(markdown_file),
                "enhanced_markdown_content": enhanced_markdown,
                "figures_directory": figures_dir,
                "processing_status": "success"
            }

            # Generate summary if requested
            if generate_summary:
                logger.info("Generating book summary using summarization factory")
                try:
                    book_summary = self._generate_book_summary(
                        enhanced_markdown, pdf_file.stem)

                    # Save summary
                    summary_file = output_path / \
                        f"{pdf_file.stem}_summary.json"
                    self.file_manager.save_book_summary(
                        book_summary, str(summary_file))

                    results["summary_status"] = "success"
                    results["summary_file_path"] = str(summary_file)

                    logger.info(f"Book summary saved to: {summary_file}")

                except Exception as e:
                    logger.warning(f"Summary generation failed: {e}")
                    results["summary_status"] = "failed"
                    results["summary_error"] = str(e)

            logger.info("PDF processing pipeline completed successfully")
            return results

        except Exception as e:
            if isinstance(e, PipelineError):
                raise
            raise PipelineError(f"Pipeline processing failed: {e}") from e

    def process_multiple_pdfs(
        self,
        pdf_paths: List[str],
        output_dir: str = "output",
        analyzer_template: str = "content_document",
        generate_summaries: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Process multiple PDFs with content understanding.

        Args:
            pdf_paths: List of paths to PDF files
            output_dir: Directory for output files
            analyzer_template: Content Understanding analyzer template name
            generate_summaries: Whether to generate book summaries

        Returns:
            Dictionary mapping PDF paths to processing results
        """
        logger.info(f"Processing {len(pdf_paths)} PDFs")

        results = {}

        for pdf_path in pdf_paths:
            try:
                logger.info(f"Processing PDF: {pdf_path}")
                pdf_name = Path(pdf_path).stem

                # Create individual output directory
                pdf_output_dir = Path(output_dir) / pdf_name
                pdf_output_dir.mkdir(exist_ok=True)

                result = self.process_pdf_with_understanding(
                    pdf_path=pdf_path,
                    output_dir=str(pdf_output_dir),
                    analyzer_template=analyzer_template,
                    generate_summary=generate_summaries
                )

                results[pdf_path] = result
                logger.info(f"Successfully processed: {pdf_path}")

            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                results[pdf_path] = {
                    "processing_status": "failed",
                    "error": str(e)
                }

        logger.info(
            f"Batch processing completed. {len([r for r in results.values() if r.get('processing_status') == 'success'])} successful, {len([r for r in results.values() if r.get('processing_status') == 'failed'])} failed")

        return results

    def _get_analyzer_template_path(self, template_name: str) -> str:
        """Get the full path to an analyzer template.

        Args:
            template_name: Name of the template (without .json extension)

        Returns:
            Full path to the template file

        Raises:
            PipelineError: If template file not found
        """
        # Check if it's already a full path
        if Path(template_name).exists():
            return template_name

        # Look in analyzer_templates directory
        template_file = Path("analyzer_templates") / f"{template_name}.json"
        if template_file.exists():
            return str(template_file)

        # Look in current directory
        template_file = Path(f"{template_name}.json")
        if template_file.exists():
            return str(template_file)

        raise PipelineError(f"Analyzer template not found: {template_name}")

    def _generate_book_summary(self, markdown_content: str, book_title: str) -> BookSummary:
        """Generate a book summary from markdown content.

        Args:
            markdown_content: Enhanced markdown content
            book_title: Title of the book

        Returns:
            BookSummary object

        Raises:
            PipelineError: If summarization fails
        """
        try:
            logger.info(f"Generating book summary for: {book_title}")
            
            # Use the summarization factory to generate summary
            book_summary = self.summarization_factory.summarize_markdown(
                markdown_content, book_title
            )
            
            logger.info(f"✅ Successfully generated summary with {len(book_summary.chapter_summaries)} chapters")
            return book_summary
            
        except Exception as e:
            raise PipelineError(f"Summary generation failed: {e}") from e

    def _split_content_into_chapters(self, content: str, book_title: str) -> List[BookChapter]:
        """Split markdown content into chapters.

        This is a simplified approach that splits on ## headers.
        Could be enhanced with more sophisticated chapter detection.

        Args:
            content: Markdown content
            book_title: Title of the book

        Returns:
            List of BookChapter objects
        """
        chapters = []
        lines = content.split('\n')

        current_chapter = None
        current_content = []
        chapter_number = 0

        for line in lines:
            # Check for chapter header (## heading)
            if line.strip().startswith('## ') and not line.strip().startswith('### '):
                # Save previous chapter
                if current_chapter and current_content:
                    current_chapter.content = '\n'.join(current_content)
                    chapters.append(current_chapter)

                # Start new chapter
                chapter_number += 1
                chapter_title = line.strip()[3:].strip()  # Remove "## "
                current_chapter = BookChapter(
                    number=chapter_number,
                    title=chapter_title,
                    content=""
                )
                current_content = []
            else:
                if current_chapter:
                    current_content.append(line)
                elif line.strip():  # Content before first chapter
                    # Create introduction chapter
                    if not chapters:
                        chapter_number += 1
                        current_chapter = BookChapter(
                            number=chapter_number,
                            title="Introduction",
                            content=""
                        )
                        current_content = [line]

        # Add final chapter
        if current_chapter and current_content:
            current_chapter.content = '\n'.join(current_content)
            chapters.append(current_chapter)

        # If no chapters found, create a single chapter with all content
        if not chapters and content.strip():
            chapters.append(BookChapter(
                number=1,
                title=book_title or "Document Content",
                content=content
            ))

        logger.info(f"Split content into {len(chapters)} chapters")
        return chapters

    def extract_figures_only(
        self,
        pdf_path: str,
        output_dir: str = "figures",
        analyzer_template: str = "content_document"
    ) -> List[str]:
        """Extract and analyze figures from PDF without full document processing.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for extracted figures
            analyzer_template: Content Understanding analyzer template name

        Returns:
            List of figure analysis results

        Raises:
            PipelineError: If figure extraction fails
        """
        try:
            logger.info(f"Extracting figures from: {pdf_path}")

            # Get analyzer template path
            analyzer_template_path = self._get_analyzer_template_path(
                analyzer_template)

            # Process with Document Intelligence to get figures
            pdf_file = Path(pdf_path)
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()

            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

            poller = self.document_processor.doc_intel_client.begin_analyze_document(
                "prebuilt-layout",
                AnalyzeDocumentRequest(bytes_source=pdf_bytes),
                output=["figures"],
                features=["ocrHighResolution"]
            )

            result = poller.result()

            if not result.figures:
                logger.info("No figures found in document")
                return []

            # Process figures
            figure_contents = self.document_processor._process_figures(
                pdf_path, result.figures, analyzer_template_path, output_dir
            )

            logger.info(
                f"Extracted and analyzed {len(figure_contents)} figures")
            return figure_contents

        except Exception as e:
            raise PipelineError(f"Figure extraction failed: {e}") from e


# Convenience function for direct usage
def process_pdf_with_content_understanding(
    pdf_path: str,
    output_dir: str = "output",
    analyzer_template: str = "content_document",
    generate_summary: bool = True,
    custom_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to process a PDF with content understanding.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory for output files
        analyzer_template: Content Understanding analyzer template name
        generate_summary: Whether to generate a book summary
        custom_filename: Custom filename for the enhanced markdown (without extension)

    Returns:
        Dictionary containing processing results
    """
    pipeline = ContentUnderstandingPipeline()
    return pipeline.process_pdf_with_understanding(
        pdf_path=pdf_path,
        output_dir=output_dir,
        analyzer_template=analyzer_template,
        generate_summary=generate_summary,
        custom_filename=custom_filename
    )
