"""
Document processing module for educational content understanding.

This module handles PDF processing, figure extraction, and enhanced
markdown generation using Azure Document Intelligence and Content Understanding.
"""

import io
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import fitz
from PIL import Image

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

from ..core.exceptions import DocumentProcessingError, ContentUnderstandingError
from ..core.config import Settings
from .client import ContentUnderstandingClient

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes documents using Azure Document Intelligence and Content Understanding."""

    def __init__(self, settings: Settings, credential):
        """Initialize document processor.

        Args:
            settings: Application settings
            credential: Azure credential for authentication
        """
        self.settings = settings
        self.credential = credential

        # Initialize Document Intelligence client
        self.doc_intel_client = DocumentIntelligenceClient(
            endpoint=settings.azure_document_intelligence_endpoint,
            api_version=settings.azure_document_intelligence_api_version,
            credential=credential
        )

        # Content Understanding client will be initialized when needed
        self._content_understanding_client = None

        logger.info("Document processor initialized")

    def _get_content_understanding_client(self) -> ContentUnderstandingClient:
        """Get or create Content Understanding client."""
        if self._content_understanding_client is None:
            from azure.identity import get_bearer_token_provider
            token_provider = get_bearer_token_provider(
                self.credential,
                "https://cognitiveservices.azure.com/.default"
            )

            self._content_understanding_client = ContentUnderstandingClient(
                endpoint=self.settings.azure_ai_service_endpoint,
                api_version=self.settings.azure_ai_service_api_version,
                token_provider=token_provider
            )

        return self._content_understanding_client

    def process_pdf_to_markdown(
        self,
        pdf_path: str,
        analyzer_template_path: Optional[str] = None,
        output_figures_dir: Optional[str] = None
    ) -> str:
        """Process PDF to enhanced markdown with figure understanding.

        Args:
            pdf_path: Path to the PDF file
            analyzer_template_path: Path to Content Understanding analyzer template
            output_figures_dir: Directory to save extracted figures

        Returns:
            Enhanced markdown content with figure descriptions

        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            logger.info(f"Processing PDF to markdown: {pdf_path}")

            # Read PDF file
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise DocumentProcessingError(
                    f"PDF file not found: {pdf_path}")

            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()

            # Analyze document layout with Document Intelligence
            logger.info("Analyzing document layout with Document Intelligence")
            poller = self.doc_intel_client.begin_analyze_document(
                "prebuilt-layout",
                AnalyzeDocumentRequest(bytes_source=pdf_bytes),
                output=["figures"],
                features=["ocrHighResolution"],
                output_content_format="markdown"
            )

            result: AnalyzeResult = poller.result()
            md_content = result.content

            # Process figures if present
            if result.figures and analyzer_template_path:
                logger.info(
                    f"Processing {len(result.figures)} figures with Content Understanding")
                figure_contents = self._process_figures(
                    pdf_path, result.figures, analyzer_template_path, output_figures_dir
                )

                # Insert figure contents into markdown
                span_offsets = [f.spans[0]["offset"] for f in result.figures]
                md_content = self._insert_figure_contents(
                    md_content, figure_contents, span_offsets)

                logger.info("Figure contents inserted into markdown")
            else:
                logger.info(
                    "No figures found or no analyzer template provided")

            logger.info(
                f"Document processing completed. Markdown length: {len(md_content):,} characters")
            return md_content

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"Failed to process PDF: {e}") from e

    def _process_figures(
        self,
        pdf_path: str,
        figures: List[Any],
        analyzer_template_path: str,
        output_figures_dir: Optional[str] = None
    ) -> List[str]:
        """Process figures using Content Understanding.

        Args:
            pdf_path: Path to the PDF file
            figures: List of figures from Document Intelligence
            analyzer_template_path: Path to analyzer template
            output_figures_dir: Directory to save figures

        Returns:
            List of formatted figure contents
        """
        # Set up analyzer
        import uuid
        analyzer_id = f"content-understanding-{uuid.uuid4()}"
        content_client = self._get_content_understanding_client()

        try:
            # Create analyzer
            content_client.create_analyzer(analyzer_id, analyzer_template_path)

            # Set up output directory
            if output_figures_dir is None:
                output_figures_dir = "figures"
            figures_dir = Path(output_figures_dir)
            figures_dir.mkdir(exist_ok=True)

            figure_contents = []

            for figure_idx, figure in enumerate(figures):
                try:
                    # Extract figure image
                    bounding_box, page_number = self._get_figure_bounds(figure)
                    cropped_img = self._crop_image_from_pdf_page(
                        pdf_path, page_number - 1, bounding_box)

                    # Save figure
                    figure_filename = f"figure_{figure_idx + 1}.png"
                    figure_filepath = figures_dir / figure_filename
                    cropped_img.save(figure_filepath)

                    # Analyze figure with Content Understanding
                    logger.debug(f"Analyzing figure {figure_idx + 1}")
                    result = content_client.analyze_image(
                        analyzer_id, str(figure_filepath))

                    # Format result
                    figure_content = self._format_content_understanding_result(
                        result)
                    figure_contents.append(figure_content)

                    logger.debug(
                        f"Figure {figure_idx + 1} processed successfully")

                except Exception as e:
                    logger.warning(
                        f"Failed to process figure {figure_idx + 1}: {e}")
                    figure_contents.append(
                        f"Figure {figure_idx + 1}: Content analysis failed")

            return figure_contents

        finally:
            # Clean up analyzer
            try:
                content_client.delete_analyzer(analyzer_id)
                logger.debug(f"Analyzer {analyzer_id} deleted")
            except Exception as e:
                logger.warning(f"Failed to delete analyzer {analyzer_id}: {e}")

    def _get_figure_bounds(self, figure: Any) -> Tuple[Tuple[float, float, float, float], int]:
        """Extract bounding box and page number from figure.

        Args:
            figure: Figure object from Document Intelligence

        Returns:
            Tuple of (bounding_box, page_number)
        """
        region = figure.bounding_regions[0]
        bounding_box = (
            region.polygon[0],  # x0 (left)
            region.polygon[1],  # y0 (top)
            region.polygon[4],  # x1 (right)
            region.polygon[5]   # y1 (bottom)
        )
        page_number = region.page_number
        return bounding_box, page_number

    def _crop_image_from_pdf_page(
        self,
        pdf_path: str,
        page_number: int,
        bounding_box: Tuple[float, float, float, float]
    ) -> Image.Image:
        """Crop a region from a PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (0-indexed)
            bounding_box: Tuple of (x0, y0, x1, y1) coordinates

        Returns:
            PIL Image of the cropped area
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_number)

            # Convert bounding box to fitz coordinates
            bbx = [x * 72 for x in bounding_box]
            rect = fitz.Rect(bbx)
            pix = page.get_pixmap(matrix=fitz.Matrix(
                300 / 72, 300 / 72), clip=rect)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()

            return img

        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to crop image from PDF: {e}") from e

    def _insert_figure_contents(
        self,
        md_content: str,
        figure_contents: List[str],
        span_offsets: List[int]
    ) -> str:
        """Insert figure contents into markdown at specified offsets.

        This function inserts the figure content for each of the provided figures in figure_contents
        before the span offset of that figure in the given markdown content.

        Args:
            md_content: Original markdown content
            figure_contents: List of figure content strings
            span_offsets: List of span offsets (must be sorted and strictly increasing)

        Returns:
            Modified markdown content with figure contents
        """
        # NOTE: In this implementation, we only alter the Markdown content returned by the Document Intelligence API,
        # and not the per-element spans in the API response. Thus, after figure content insertion, these per-element spans will be inaccurate.
        # This may impact use cases like citation page number calculation.
        # Additional code may be needed to correct the spans or otherwise infer the page numbers for each citation.

        # Validate span_offsets are sorted and strictly increasing
        if span_offsets != sorted(span_offsets) or not all(
            o < span_offsets[i + 1] for i, o in enumerate(span_offsets)
            if i < len(span_offsets) - 1
        ):
            raise ValueError(
                "span_offsets should be sorted and strictly increasing")

        # Split the content based on the provided spans
        parts = []
        preamble = None

        for i, offset in enumerate(span_offsets):
            if i == 0 and offset > 0:
                preamble = md_content[0:offset]
                # Check if we have more than one span before accessing [i + 1]
                if i < len(span_offsets) - 1:
                    parts.append(md_content[offset:span_offsets[i + 1]])
                else:
                    parts.append(md_content[offset:])
            elif i == len(span_offsets) - 1:
                parts.append(md_content[offset:])
            else:
                parts.append(md_content[offset:span_offsets[i + 1]])

        # Join the parts back together with the figure content inserted
        modified_content = ""
        if preamble:
            modified_content += preamble

        for i, part in enumerate(parts):
            modified_content += f'<!-- FigureContent="{figure_contents[i]}" -->' + part

        return modified_content

    def _format_content_understanding_result(self, content_understanding_result: Dict[str, Any]) -> str:
        """Format Content Understanding result as markdown.

        Args:
            content_understanding_result: Result from Content Understanding API

        Returns:
            Formatted markdown string
        """
        def _format_result(key: str, result: Dict[str, Any]) -> str:
            result_type = result["type"]
            if result_type in ["string", "integer", "number", "boolean"]:
                return f"**{key}**: " + str(result[f'value{result_type.capitalize()}']) + "\\n"
            elif result_type == "array":
                values = [
                    str(result["valueArray"][i]
                        [f"value{r['type'].capitalize()}"])
                    for i, r in enumerate(result["valueArray"])
                ]
                return f"**{key}**: " + ', '.join(values) + "\\n"
            elif result_type == "object":
                sub_results = ''.join([
                    _format_result(f"{key}.{k}", result["valueObject"][k])
                    for k in result["valueObject"]
                ])
                return f"**{key}**\\n" + sub_results
            return ""

        try:
            logger.debug(
                f"Content Understanding result keys: {list(content_understanding_result.keys())}")
            if 'result' in content_understanding_result:
                logger.debug(
                    f"Result keys: {list(content_understanding_result['result'].keys())}")
                if 'contents' in content_understanding_result['result']:
                    logger.debug(
                        f"Contents length: {len(content_understanding_result['result']['contents'])}")
                    if content_understanding_result['result']['contents']:
                        logger.debug(
                            f"First content keys: {list(content_understanding_result['result']['contents'][0].keys())}")

            # Handle the actual Content Understanding API response structure
            contents = content_understanding_result['result']['contents']
            if not contents:
                return "No content found in Content Understanding result"

            # The Content Understanding API returns markdown content directly
            first_content = contents[0]
            if 'markdown' in first_content:
                # Clean up the markdown content
                markdown_content = first_content['markdown']
                # Remove the outer <figure> tags since we're inserting this into an existing figure
                markdown_content = markdown_content.replace(
                    '<figure>', '').replace('</figure>', '')
                # Clean up extra whitespace
                markdown_content = markdown_content.strip()
                return markdown_content
            elif 'fields' in first_content:
                # Legacy handling for field-based responses
                fields = first_content['fields']
                markdown_result = ""
                for field_name in fields:
                    markdown_result += _format_result(
                        field_name, fields[field_name])
                return markdown_result
            else:
                return f"Unsupported content structure: {list(first_content.keys())}"

        except (KeyError, IndexError) as e:
            logger.warning(
                f"Failed to format Content Understanding result: {e}")
            logger.warning(
                f"Content Understanding result structure: {content_understanding_result}")
            return "Content analysis result formatting failed"
