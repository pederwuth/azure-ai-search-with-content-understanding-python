"""
Enhanced Document Processing with Rich Content Understanding.

This module provides the exact same high-quality processing as the notebook
'search_with_visual_document.ipynb' but packaged as a reusable Python API.

The key difference from the existing pipeline is that this implementation
follows the notebook's approach exactly to ensure identical output quality.
"""

import io
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.exceptions import ServiceRequestTimeoutError

from python.content_understanding_client import AzureContentUnderstandingClient

logger = logging.getLogger(__name__)


class EnhancedDocumentProcessor:
    """Document processor that follows the notebook approach for maximum quality."""

    # Timeout configuration (in minutes)
    MAX_DOCUMENT_ANALYSIS_TIMEOUT_MINUTES = 15
    MAX_FIGURE_PROCESSING_TIMEOUT_MINUTES = 30
    MAX_PER_FIGURE_TIMEOUT_SECONDS = 300  # 5 minutes per figure

    def __init__(self):
        """Initialize the enhanced document processor."""
        # Load configuration from environment
        self.azure_ai_service_endpoint = os.getenv("AZURE_AI_SERVICE_ENDPOINT")
        self.azure_ai_service_api_version = os.getenv(
            "AZURE_AI_SERVICE_API_VERSION", "2024-12-01-preview")
        self.azure_document_intelligence_api_version = os.getenv(
            "AZURE_DOCUMENT_INTELLIGENCE_API_VERSION", "2024-11-30")

        if not self.azure_ai_service_endpoint:
            raise ValueError(
                "AZURE_AI_SERVICE_ENDPOINT environment variable is required")

        # Initialize Azure credentials
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential,
            "https://cognitiveservices.azure.com/.default"
        )

        # Initialize clients (will be created per request to ensure fresh connections)
        self._content_understanding_client = None
        self._document_intelligence_client = None

        logger.info("Enhanced document processor initialized")

    def _get_content_understanding_client(self) -> AzureContentUnderstandingClient:
        """Get or create Content Understanding client."""
        if self._content_understanding_client is None:
            self._content_understanding_client = AzureContentUnderstandingClient(
                endpoint=self.azure_ai_service_endpoint,
                api_version=self.azure_ai_service_api_version,
                token_provider=self.token_provider,
                x_ms_useragent="azure-ai-content-understanding-python/enhanced_document_processor"
            )
        return self._content_understanding_client

    def _get_document_intelligence_client(self) -> DocumentIntelligenceClient:
        """Get or create Document Intelligence client."""
        if self._document_intelligence_client is None:
            self._document_intelligence_client = DocumentIntelligenceClient(
                endpoint=self.azure_ai_service_endpoint,
                api_version=self.azure_document_intelligence_api_version,
                credential=self.credential,
                output=str('figures')
            )
        return self._document_intelligence_client

    def insert_figure_contents(self, md_content: str, figure_contents: List[str], span_offsets: List[int]) -> str:
        """
        Insert figure content before the span offset of each figure in the markdown content.

        Args:
            md_content: The original markdown content
            figure_contents: The contents of each figure to insert
            span_offsets: The span offsets of each figure in order (must be sorted and strictly increasing)

        Returns:
            The modified markdown content with figure contents prepended to each figure's span

        Note:
            This alters only the Markdown content and not the per-element spans in the API response.
            After figure content insertion, per-element spans will be inaccurate.
        """
        # Validate span_offsets are sorted and strictly increasing
        if span_offsets != sorted(span_offsets) or not all([
            o < span_offsets[i + 1] for i, o in enumerate(span_offsets) if i < len(span_offsets) - 1
        ]):
            raise ValueError(
                "span_offsets should be sorted and strictly increasing.")

        # Split the content based on the provided spans
        parts = []
        preamble = None
        for i, offset in enumerate(span_offsets):
            if i == 0 and offset > 0:
                preamble = md_content[0:offset]

            if i == len(span_offsets) - 1:
                # Last figure - take content from this offset to end
                parts.append(md_content[offset:])
            else:
                # Not last figure - take content from this offset to next offset
                parts.append(md_content[offset:span_offsets[i + 1]])

        # Join the parts back together with the figure content inserted
        modified_content = ""
        if preamble:
            modified_content += preamble
        for i, part in enumerate(parts):
            modified_content += f"<!-- FigureContent=\"{figure_contents[i]}\" -->" + part

        return modified_content

    def crop_image_from_pdf_page(self, pdf_path: Path, page_number: int, bounding_box: Tuple[float, float, float, float]) -> Image.Image:
        """
        Crop a region from a given page in a PDF and return it as a PIL Image.

        Args:
            pdf_path: Path to the PDF file
            page_number: The page number to crop from (0-indexed)
            bounding_box: A tuple of (x0, y0, x1, y1) coordinates for the bounding box

        Returns:
            A PIL Image of the cropped area
        """
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number)

        # Cropping the page. The rect requires the coordinates in the format (x0, y0, x1, y1).
        bbx = [x * 72 for x in bounding_box]
        rect = fitz.Rect(bbx)
        pix = page.get_pixmap(matrix=fitz.Matrix(
            300 / 72, 300 / 72), clip=rect)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        doc.close()
        return img

    def format_content_understanding_result(self, content_understanding_result: Dict[str, Any]) -> str:
        """
        Format the JSON output of the Content Understanding result as Markdown for downstream usage.

        Args:
            content_understanding_result: A dictionary containing the output from Content Understanding

        Returns:
            A Markdown string of the result content
        """
        def _format_result(key: str, result: Dict[str, Any]) -> str:
            result_type = result.get("type", "string")

            if result_type in ["string", "integer", "number", "boolean"]:
                value_key = f'value{result_type.capitalize()}'
                if value_key in result:
                    return f"**{key}**: " + str(result[value_key]) + "\n"
                else:
                    # Fallback to any available value
                    for fallback_key in ['valueString', 'value', 'content']:
                        if fallback_key in result:
                            return f"**{key}**: " + str(result[fallback_key]) + "\n"
                    return f"**{key}**: [No value found]\n"

            elif result_type == "array":
                if "valueArray" in result and result["valueArray"]:
                    try:
                        return f"**{key}**: " + ', '.join([
                            str(result["valueArray"][i].get(f"value{r.get('type', 'String').capitalize()}",
                                                            result["valueArray"][i].get('valueString',
                                                                                        result["valueArray"][i].get('value', str(result["valueArray"][i])))))
                            for i, r in enumerate(result["valueArray"])
                        ]) + "\n"
                    except (KeyError, IndexError, TypeError) as e:
                        logger.warning(
                            f"Error processing array field {key}: {e}. Raw result: {result}")
                        return f"**{key}**: [Array processing error: {str(e)}]\n"
                else:
                    return f"**{key}**: [Empty array or no valueArray key]\n"

            elif result_type == "object":
                if "valueObject" in result:
                    return f"**{key}**\n" + ''.join([
                        _format_result(f"{key}.{k}", result["valueObject"][k])
                        for k in result["valueObject"]
                    ])
                else:
                    return f"**{key}**: [No valueObject key found]\n"

            return f"**{key}**: [Unknown type: {result_type}]\n"

        fields = content_understanding_result['result']['contents'][0]['fields']
        markdown_result = ""
        for field in fields:
            markdown_result += _format_result(field, fields[field])

        return markdown_result

    def create_analyzer(self, analyzer_template_path: str = "analyzer_templates/image_chart_diagram_understanding.json") -> str:
        """
        Create a Content Understanding analyzer.

        Args:
            analyzer_template_path: Path to the analyzer template JSON file

        Returns:
            The analyzer ID

        Raises:
            Exception: If analyzer creation fails
        """
        content_understanding_client = self._get_content_understanding_client()

        analyzer_id = "enhanced-content-understanding-" + str(uuid.uuid4())

        try:
            response = content_understanding_client.begin_create_analyzer(
                analyzer_id,
                analyzer_template_path=analyzer_template_path
            )
            result = content_understanding_client.poll_result(response)

            logger.info(f"Created analyzer: {analyzer_id}")
            logger.debug(f"Analyzer details: {json.dumps(result, indent=2)}")

            return analyzer_id

        except Exception as e:
            logger.error(f"Error creating analyzer {analyzer_id}: {e}")
            raise

    def _extract_book_title_from_content(self, document_result) -> Optional[str]:
        """
        Extract book title from Document Intelligence result.

        Args:
            document_result: Result from Document Intelligence analysis

        Returns:
            Extracted book title or None if not found
        """
        try:
            # Look for title in various places in the document structure
            if hasattr(document_result, 'pages') and document_result.pages:
                first_page = document_result.pages[0]

                # Look for the largest text on the first page (likely title)
                if hasattr(first_page, 'lines') and first_page.lines:
                    # Get text from first few lines and find the longest/most prominent one
                    potential_titles = []
                    # Check first 5 lines
                    for i, line in enumerate(first_page.lines[:5]):
                        if hasattr(line, 'content'):
                            text = line.content.strip()
                            # Skip if it looks like metadata, page numbers, or too short
                            if (len(text) > 5 and
                                not text.isdigit() and
                                not text.lower().startswith(('page', 'chapter', 'www', 'http')) and
                                not '©' in text and
                                    len(text.split()) > 1):  # Multi-word titles preferred
                                potential_titles.append(text)

                    if potential_titles:
                        # Return the first good candidate
                        title = potential_titles[0]
                        # Clean up the title
                        title = title.replace('\n', ' ').replace('\r', ' ')
                        title = ' '.join(title.split())  # Normalize whitespace
                        return title[:50]  # Limit length

            # Fallback: look in document-level content if available
            if hasattr(document_result, 'content') and document_result.content:
                lines = document_result.content.split(
                    '\n')[:10]  # First 10 lines
                for line in lines:
                    line = line.strip()
                    if (len(line) > 10 and
                        len(line) < 100 and
                        not line.isdigit() and
                            len(line.split()) > 2):  # Multi-word title
                        return line[:50]

        except Exception as e:
            logger.warning(
                f"Failed to extract title from document content: {e}")

        return None

    def process_pdf_with_enhanced_understanding(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        analyzer_template_path: str = "analyzer_templates/image_chart_diagram_understanding.json",
        custom_filename: Optional[str] = None,
        use_content_books_structure: bool = False,
        content_type: str = "book",
        original_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF with enhanced content understanding following the notebook approach.

        Args:
            pdf_path: Path to the PDF file (may be temporary)
            output_dir: Directory for output files
            analyzer_template_path: Path to the analyzer template
            custom_filename: Custom filename for output (without extension)
            use_content_books_structure: Whether to use the /content/books structure
            content_type: Type of content being processed (e.g., "book")
            original_filename: Original filename of the uploaded PDF (for saving purposes)

        Returns:
            Dictionary containing processing results with same structure as notebook
        """
        import datetime

        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Determine initial book title from custom_filename, original_filename, or PDF name
        # If none provided, we'll extract it from document content later
        extract_title_from_content = False
        if custom_filename:
            book_title = custom_filename.lower().replace(' ', '_').replace('-', '_')
        elif original_filename and not original_filename.startswith('tmp'):
            # Use original filename (strip .pdf extension) if it's not a temporary name
            original_stem = Path(original_filename).stem
            book_title = original_stem.lower().replace(' ', '_').replace('-', '_')
        else:
            # No meaningful filename provided - we'll extract from document content
            book_title = pdf_file.stem.lower().replace(' ', '_').replace('-', '_')
            extract_title_from_content = True

        # Generate timestamp and job ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = str(uuid.uuid4()).split('-')[0]

        if use_content_books_structure:
            # Create structure: {book_title}-{content_type}-{timestamp}-{job_id}
            main_folder_name = f"{book_title}-{content_type}-{timestamp}-{job_id}"
            main_output_path = Path(output_dir) / main_folder_name

            # Create folder structure
            input_dir = main_output_path / "input"
            processed_dir = main_output_path / "processed"
            markdown_dir = processed_dir / \
                f"{book_title}-{content_type}-markdown-{timestamp}-{job_id}"
            figures_dir = markdown_dir / \
                f"{book_title}-{content_type}-figures-{timestamp}-{job_id}"

            # Create all directories
            main_output_path.mkdir(parents=True, exist_ok=True)
            input_dir.mkdir(exist_ok=True)
            processed_dir.mkdir(exist_ok=True)
            markdown_dir.mkdir(exist_ok=True)
            figures_dir.mkdir(exist_ok=True)

            # Copy input PDF to input directory with original filename
            import shutil
            if original_filename:
                input_pdf_path = input_dir / original_filename
            else:
                input_pdf_path = input_dir / pdf_file.name
            shutil.copy2(pdf_file, input_pdf_path)

            output_path = markdown_dir
        else:
            # Use original simple structure
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            figures_dir = output_path / "figures"
            figures_dir.mkdir(exist_ok=True)
            main_output_path = output_path
            processed_dir = output_path
            timestamp = None
            job_id = None

        logger.info(f"Processing PDF: {book_title} (from {pdf_file.name})")
        logger.info(f"Output directory: {output_path}")

        # Step 1: Create Content Understanding analyzer
        analyzer_id = self.create_analyzer(analyzer_template_path)

        try:
            # Step 2: Process document with Document Intelligence
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()

            document_intelligence_client = self._get_document_intelligence_client()
            content_understanding_client = self._get_content_understanding_client()

            logger.info(
                "Analyzing document layout with Document Intelligence...")
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-layout",
                AnalyzeDocumentRequest(bytes_source=pdf_bytes),
                output=[str('figures')],
                features=['ocrHighResolution'],
                output_content_format="markdown"
            )

            # Add timeout protection for document analysis
            start_time = time.time()

            logger.info(
                f"Waiting for document analysis to complete (max {self.MAX_DOCUMENT_ANALYSIS_TIMEOUT_MINUTES} minutes)...")

            try:
                result: AnalyzeResult = poller.result(
                    timeout=self.MAX_DOCUMENT_ANALYSIS_TIMEOUT_MINUTES * 60)
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Document analysis completed successfully in {elapsed_time:.1f} seconds")
            except Exception as e:
                elapsed_time = time.time() - start_time
                if elapsed_time >= self.MAX_DOCUMENT_ANALYSIS_TIMEOUT_MINUTES * 60:
                    error_msg = f"Document analysis timed out after {self.MAX_DOCUMENT_ANALYSIS_TIMEOUT_MINUTES} minutes. This may indicate an Azure service issue."
                    logger.error(error_msg)
                    raise TimeoutError(error_msg) from e
                else:
                    logger.error(
                        f"Document analysis failed after {elapsed_time:.1f} seconds: {e}")
                    raise
            md_content = result.content

            # Extract book title from document content if needed
            if extract_title_from_content:
                extracted_title = self._extract_book_title_from_content(result)
                if extracted_title:
                    logger.info(
                        f"📖 Extracted book title from content: '{extracted_title}'")
                    # Clean up the extracted title for use as filename
                    cleaned_title = extracted_title.lower().replace(' ', '_').replace('-', '_')
                    # Remove special characters that might cause issues
                    import re
                    cleaned_title = re.sub(
                        r'[^\w\s-]', '', cleaned_title).strip()
                    cleaned_title = re.sub(r'[-\s]+', '_', cleaned_title)

                    # Only use if meaningful
                    if cleaned_title and len(cleaned_title) > 3:
                        old_book_title = book_title
                        book_title = cleaned_title
                        logger.info(
                            f"📝 Updated book title from '{old_book_title}' to '{book_title}'")

            # Step 3: Process figures with Content Understanding
            figure_contents = []
            if result.figures:
                logger.info(
                    f"Extracting content for {len(result.figures)} figures with Content Understanding...")

                # Add timeout protection for figure processing
                figure_start_time = time.time()

                for figure_idx, figure in enumerate(result.figures):
                    # Check if we've exceeded the overall timeout
                    elapsed_time = time.time() - figure_start_time
                    if elapsed_time >= self.MAX_FIGURE_PROCESSING_TIMEOUT_MINUTES * 60:
                        error_msg = f"Figure processing timed out after {self.MAX_FIGURE_PROCESSING_TIMEOUT_MINUTES} minutes at figure {figure_idx + 1}/{len(result.figures)}"
                        logger.error(error_msg)
                        raise TimeoutError(error_msg)

                    # Get bounding box from first region
                    region = figure.bounding_regions[0]
                    bounding_box = (
                        region.polygon[0],  # x0 (left)
                        region.polygon[1],  # y0 (top)
                        region.polygon[4],  # x1 (right)
                        region.polygon[5]   # y1 (bottom)
                    )

                    page_number = region.page_number

                    # Crop image from PDF
                    cropped_img = self.crop_image_from_pdf_page(
                        pdf_file, page_number - 1, bounding_box)

                    # Save figure image
                    figure_filename = f"figure_{figure_idx + 1}.png"
                    figure_filepath = figures_dir / figure_filename
                    cropped_img.save(figure_filepath)

                    # Analyze figure with Content Understanding
                    logger.info(
                        f"Analyzing figure {figure_idx + 1}/{len(result.figures)}")

                    try:
                        content_understanding_response = content_understanding_client.begin_analyze(
                            analyzer_id,
                            str(figure_filepath)
                        )
                        content_understanding_result = content_understanding_client.poll_result(
                            content_understanding_response,
                            timeout_seconds=300  # 5 minutes per figure max
                        )

                        # Format the result
                        figure_content = self.format_content_understanding_result(
                            content_understanding_result)
                        figure_contents.append(figure_content)

                        logger.info(
                            f"Figure {figure_idx + 1} content extracted successfully")
                        logger.debug(
                            f"Figure {figure_idx + 1} content:\n{figure_content}")

                    except Exception as e:
                        logger.warning(
                            f"Failed to process figure {figure_idx + 1}: {e}. Continuing with empty content.")
                        # Add empty content to maintain figure order
                        figure_contents.append("")

                # Step 4: Insert figure content into markdown
                logger.info("Inserting figure content into document...")
                md_content = self.insert_figure_contents(
                    md_content,
                    figure_contents,
                    [f.spans[0]["offset"] for f in result.figures]
                )

            # Step 5: Save enhanced markdown
            if use_content_books_structure:
                enhanced_filename = f"{book_title}-{content_type}-markdown-{timestamp}-{job_id}.md"
            elif custom_filename:
                enhanced_filename = f"{custom_filename}.md"
            else:
                base_name = pdf_file.stem
                enhanced_filename = f"{base_name}_enhanced.md"

            enhanced_path = output_path / enhanced_filename

            with open(enhanced_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Step 6: Save cache file (same format as notebook)
            result.content = md_content
            cache_data = {
                'analyzeResult': result.as_dict()
            }

            if use_content_books_structure:
                cache_filename = f"{book_title}-{content_type}-cache-{timestamp}-{job_id}.json"
                cache_path = processed_dir / cache_filename
            else:
                cache_path = output_path / f"{pdf_file.stem}_cache.json"

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            # Create metadata file for content/books structure
            if use_content_books_structure:
                metadata = {
                    "job_id": job_id,
                    "book_title": book_title,
                    "content_type": content_type,
                    "created_at": datetime.datetime.now().isoformat() + "Z",
                    "status": "completed",
                    "input_file": pdf_file.name,
                    "processing_pipeline": "enhanced_document_processor",
                    "folder_structure": "v1",
                    "naming_convention": "{book_title}-{content_type}-{subtype}-{timestamp}-{job_id}",
                    "output_files": {
                        "enhanced_markdown": f"processed/{markdown_dir.name}/{enhanced_filename}",
                        "cache_file": f"processed/{cache_filename}",
                        "figures_directory": f"processed/{markdown_dir.name}/{figures_dir.name}/",
                        "input_pdf": f"input/{pdf_file.name}"
                    },
                    "statistics": {
                        "total_pages": len(result.pages) if result.pages else 0,
                        "figures_extracted": len(result.figures) if result.figures else 0,
                        "processing_time_seconds": 0,  # Could be calculated if needed
                        "markdown_characters": len(md_content),
                        "estimated_tokens": int(len(md_content.split()) * 1.3)
                    }
                }

                metadata_path = main_output_path / "metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

            # Prepare results
            processing_results = {
                "pdf_file": str(pdf_file),
                "enhanced_markdown": str(enhanced_path),
                "cache_file": str(cache_path),
                "figures_directory": str(figures_dir),
                "figures_processed": len(result.figures) if result.figures else 0,
                "document_length": len(md_content),
                "analyzer_id": analyzer_id,
                "processing_stats": {
                    "total_figures": len(result.figures) if result.figures else 0,
                    "figures_with_content": len(figure_contents),
                    "markdown_characters": len(md_content),
                    "estimated_tokens": int(len(md_content.split()) * 1.3)
                }
            }

            # Add structure-specific information
            if use_content_books_structure:
                processing_results.update({
                    "main_folder": str(main_output_path),
                    "job_id": job_id,
                    "timestamp": timestamp,
                    "content_type": content_type,
                    "book_title": book_title,
                    "metadata_file": str(main_output_path / "metadata.json"),
                    "input_directory": str(main_output_path / "input"),
                    "processed_directory": str(processed_dir),
                    "markdown_directory": str(markdown_dir),
                    "folder_structure": "content_books_v1"
                })

            logger.info("✅ Enhanced document processing complete!")
            logger.info(f"📄 Document: {book_title} (from {pdf_file.name})")
            logger.info(
                f"📚 Figures processed: {processing_results['figures_processed']}")
            logger.info(
                f"📝 Markdown length: {processing_results['document_length']:,} characters")
            logger.info(
                f"🧮 Estimated tokens: {processing_results['processing_stats']['estimated_tokens']:,}")
            logger.info(f"💾 Enhanced markdown saved to: {enhanced_path}")

            return processing_results

        except Exception as e:
            logger.error(f"Error during enhanced document processing: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        finally:
            # Clean up analyzer
            try:
                content_understanding_client = self._get_content_understanding_client()
                content_understanding_client.delete_analyzer(analyzer_id)
                logger.info(f"Cleaned up analyzer: {analyzer_id}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up analyzer {analyzer_id}: {e}")


def process_pdf_with_notebook_quality(
    pdf_path: str | Path,
    output_dir: str | Path = "output",
    analyzer_template_path: str = "analyzer_templates/image_chart_diagram_understanding.json",
    custom_filename: Optional[str] = None,
    use_content_books_structure: bool = False,
    content_type: str = "book",
    original_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a PDF with the same quality as the notebook.

    Args:
        pdf_path: Path to the PDF file (may be temporary)
        output_dir: Directory for output files
        analyzer_template_path: Path to the analyzer template
        custom_filename: Custom filename for output (without extension)
        use_content_books_structure: Whether to use the /content/books structure
        content_type: Type of content being processed (e.g., "book")
        original_filename: Original filename of the uploaded PDF (for saving purposes)

    Returns:
        Dictionary containing processing results
    """
    processor = EnhancedDocumentProcessor()
    return processor.process_pdf_with_enhanced_understanding(
        pdf_path=pdf_path,
        output_dir=output_dir,
        analyzer_template_path=analyzer_template_path,
        custom_filename=custom_filename,
        use_content_books_structure=use_content_books_structure,
        content_type=content_type,
        original_filename=original_filename
    )
