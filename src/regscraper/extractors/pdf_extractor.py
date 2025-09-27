"""PDF text extraction with OCR fallback."""

import io
from typing import BinaryIO
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from .base import TextExtractor
from ..logging import logger


class PdfExtractor(TextExtractor):
    """Extracts text from PDF files with OCR fallback for image-based PDFs."""

    def __init__(self, ocr_dpi: int = 300):
        self.ocr_dpi = ocr_dpi

    async def extract_text(self, content: bytes | BinaryIO) -> str:
        """Extract text from PDF content with OCR fallback for images."""
        logger.debug("Extracting text from PDF")

        # Handle both bytes and BinaryIO
        if isinstance(content, bytes):
            stream = io.BytesIO(content)
        else:
            stream = content

        text_parts: list[str] = []

        try:
            doc = fitz.open(stream=stream, filetype="pdf")

            for page_num, page in enumerate(doc, 1):
                # Try direct text extraction first
                text = page.get_text("text")

                if text.strip():
                    text_parts.append(text)
                    logger.debug(f"Extracted text from PDF page {page_num} (direct)")
                else:
                    # Fallback to OCR for image-based content
                    logger.debug(f"No direct text found on page {page_num}, trying OCR")
                    ocr_text = await self._ocr_page(page)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)
                        logger.debug(f"Extracted text from PDF page {page_num} (OCR)")

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

        extracted_text = "\n".join(text_parts).strip()
        logger.debug(f"Extracted {len(extracted_text)} characters from PDF")
        return extracted_text

    async def _ocr_page(self, page) -> str:
        """Perform OCR on a PDF page."""
        try:
            # Render page to image
            pix = page.get_pixmap(dpi=self.ocr_dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Extract text using OCR
            return pytesseract.image_to_string(img)

        except Exception as e:
            logger.warning(f"OCR failed for page: {e}")
            return ""

    def supports_format(self, file_extension: str) -> bool:
        """Check if this extractor supports PDF files."""
        return file_extension.lower() in [".pdf"]


# Default instance
default_pdf_extractor = PdfExtractor()
