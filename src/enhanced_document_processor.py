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
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

from python.content_understanding_client import AzureContentUnderstandingClient

logger = logging.getLogger(__name__)


class EnhancedDocumentProcessor:
    """Document processor that follows the notebook approach for maximum quality."""

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
            result_type = result["type"]
            if result_type in ["string", "integer", "number", "boolean"]:
                return f"**{key}**: " + str(result[f'value{result_type.capitalize()}']) + "\n"
            elif result_type == "array":
                return f"**{key}**: " + ', '.join([
                    str(result["valueArray"][i]
                        [f"value{r['type'].capitalize()}"])
                    for i, r in enumerate(result["valueArray"])
                ]) + "\n"
            elif result_type == "object":
                return f"**{key}**\n" + ''.join([
                    _format_result(f"{key}.{k}", result["valueObject"][k])
                    for k in result["valueObject"]
                ])
            return ""

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

    def process_pdf_with_enhanced_understanding(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        analyzer_template_path: str = "analyzer_templates/image_chart_diagram_understanding.json",
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF with enhanced content understanding following the notebook approach.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output files
            analyzer_template_path: Path to the analyzer template
            custom_filename: Custom filename for output (without extension)

        Returns:
            Dictionary containing processing results with same structure as notebook
        """
        pdf_file = Path(pdf_path)
        output_path = Path(output_dir)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        figures_dir = output_path / "figures"
        figures_dir.mkdir(exist_ok=True)

        logger.info(f"Processing PDF: {pdf_file.name}")
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

            result: AnalyzeResult = poller.result()
            md_content = result.content

            # Step 3: Process figures with Content Understanding
            figure_contents = []
            if result.figures:
                logger.info(
                    f"Extracting content for {len(result.figures)} figures with Content Understanding...")

                for figure_idx, figure in enumerate(result.figures):
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

                    content_understanding_response = content_understanding_client.begin_analyze(
                        analyzer_id,
                        str(figure_filepath)
                    )
                    content_understanding_result = content_understanding_client.poll_result(
                        content_understanding_response,
                        timeout_seconds=1000
                    )

                    # Format the result
                    figure_content = self.format_content_understanding_result(
                        content_understanding_result)
                    figure_contents.append(figure_content)

                    logger.info(
                        f"Figure {figure_idx + 1} content extracted successfully")
                    logger.debug(
                        f"Figure {figure_idx + 1} content:\n{figure_content}")

                # Step 4: Insert figure content into markdown
                logger.info("Inserting figure content into document...")
                md_content = self.insert_figure_contents(
                    md_content,
                    figure_contents,
                    [f.spans[0]["offset"] for f in result.figures]
                )

            # Step 5: Save enhanced markdown
            if custom_filename:
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

            cache_path = output_path / f"{pdf_file.stem}_cache.json"
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

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

            logger.info("✅ Enhanced document processing complete!")
            logger.info(f"📄 Document: {pdf_file.name}")
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
    custom_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a PDF with the same quality as the notebook.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory for output files
        analyzer_template_path: Path to the analyzer template
        custom_filename: Custom filename for output (without extension)

    Returns:
        Dictionary containing processing results
    """
    processor = EnhancedDocumentProcessor()
    return processor.process_pdf_with_enhanced_understanding(
        pdf_path=pdf_path,
        output_dir=output_dir,
        analyzer_template_path=analyzer_template_path,
        custom_filename=custom_filename
    )
