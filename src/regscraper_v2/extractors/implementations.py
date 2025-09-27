"""Text extractor implementations for different document types."""

import io
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from docx import Document as DocxDocument
import mammoth
import trafilatura

from ..interfaces import TextExtractor, DownloadResult, ExtractionResult, ContentType


class PdfTextExtractor(TextExtractor):
    """Extracts text from PDF documents with OCR fallback."""

    def __init__(self, ocr_dpi: int = 300):
        self.ocr_dpi = ocr_dpi

    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract text from PDF content with OCR fallback."""
        text_parts = []
        metadata = {"pages_processed": 0, "ocr_pages": 0}

        try:
            doc = fitz.open(stream=io.BytesIO(download_result.content), filetype="pdf")

            for page_num, page in enumerate(doc, 1):
                # Try direct text extraction first
                text = page.get_text("text")

                if text.strip():
                    text_parts.append(text)
                else:
                    # OCR fallback for image-based content
                    ocr_text = await self._ocr_page(page)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)
                        metadata["ocr_pages"] += 1

                metadata["pages_processed"] = page_num

            doc.close()

        except Exception as e:
            raise RuntimeError(f"PDF text extraction failed: {e}")

        full_text = "\\n".join(text_parts).strip()
        return ExtractionResult(full_text, metadata)

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle PDF content."""
        return content_type == ContentType.PDF

    async def _ocr_page(self, page) -> str:
        """Perform OCR on a PDF page."""
        try:
            pix = page.get_pixmap(dpi=self.ocr_dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return pytesseract.image_to_string(img)
        except Exception:
            return ""


class DocxTextExtractor(TextExtractor):
    """Extracts text from DOCX and DOC documents."""

    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract text from DOCX/DOC content."""
        metadata = {"format": "unknown", "paragraphs": 0}

        try:
            content_stream = io.BytesIO(download_result.content)

            # Detect if it's a legacy DOC file by URL or content sniffing
            is_doc_format = download_result.url.lower().endswith(
                ".doc"
            ) or self._is_legacy_doc_format(download_result.content)

            if is_doc_format:
                # Use mammoth for .doc files
                result = mammoth.extract_raw_text(content_stream)
                text = (result.value or "").strip()
                metadata["format"] = "doc"

                if result.messages:
                    metadata["conversion_warnings"] = len(result.messages)
            else:
                # Use python-docx for .docx files
                doc = DocxDocument(content_stream)
                paragraphs = [
                    p.text for p in doc.paragraphs if p.text and p.text.strip()
                ]
                text = "\\n".join(paragraphs)
                metadata["format"] = "docx"
                metadata["paragraphs"] = len(paragraphs)

        except Exception as e:
            raise RuntimeError(f"DOCX text extraction failed: {e}")

        return ExtractionResult(text, metadata)

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle DOCX content."""
        return content_type == ContentType.DOCX

    def _is_legacy_doc_format(self, content: bytes) -> bool:
        """Heuristic to detect legacy DOC format."""
        # DOC files typically start with specific signatures
        doc_signatures = [
            b"\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1",  # OLE2 signature
            b"\\xdb\\xa5-\\x00\\x00\\x00",  # Alternative DOC signature
        ]

        return any(content.startswith(sig) for sig in doc_signatures)


class HtmlTextExtractor(TextExtractor):
    """Extracts clean text from HTML documents."""

    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract clean text from HTML content using trafilatura."""
        try:
            html_content = download_result.content.decode("utf-8", errors="ignore")

            # Use trafilatura for clean text extraction
            extracted_text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            extraction_method = "trafilatura"
            if not extracted_text:
                # Fallback: try basic text extraction
                extracted_text = self._basic_html_extraction(html_content)
                extraction_method = "basic"

            metadata = {
                "original_length": len(html_content),
                "extraction_method": extraction_method,
            }

            return ExtractionResult(extracted_text or "", metadata)

        except Exception as e:
            raise RuntimeError(f"HTML text extraction failed: {e}")

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle HTML content."""
        return content_type == ContentType.HTML

    def _basic_html_extraction(self, html_content: str) -> str:
        """Basic HTML text extraction as fallback."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.decompose()

            return soup.get_text(separator="\\n", strip=True)

        except ImportError:
            # If BeautifulSoup is not available, use very basic extraction
            import re

            # Remove HTML tags (very basic approach)
            clean_text = re.sub(r"<[^>]+>", " ", html_content)
            # Clean up whitespace
            clean_text = re.sub(r"\\s+", " ", clean_text)
            return clean_text.strip()
