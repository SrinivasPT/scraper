from __future__ import annotations

import io

import fitz  # type: ignore[import-untyped] # PyMuPDF
import pytesseract  # type: ignore[import-untyped]
from PIL import Image

from regscraper.interfaces import ContentType, DownloadResult, ExtractionResult, TextExtractor


class PdfTextExtractor(TextExtractor):
    """Extracts text from PDF documents with OCR fallback."""

    def __init__(self, ocr_dpi: int = 300) -> None:
        self.ocr_dpi = ocr_dpi

    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract text from PDF content with OCR fallback."""
        text_parts: list[str] = []
        metadata: dict[str, int] = {"pages_processed": 0, "ocr_pages": 0}

        try:
            doc = fitz.open(stream=io.BytesIO(download_result.content), filetype="pdf")  # type: ignore[misc]

            for page_num in range(len(doc)):  # Use range instead of enumerate
                page = doc[page_num]  # Get page by index
                # Try direct text extraction first
                text: str = str(page.get_text("text"))  # type: ignore[misc]

                if text.strip():
                    text_parts.append(text)
                else:
                    # OCR fallback for image-based content
                    ocr_text = await self._ocr_page(page)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)
                        metadata["ocr_pages"] += 1

                metadata["pages_processed"] = page_num + 1

            doc.close()  # type: ignore[misc]

        except (OSError, ValueError) as e:
            msg = f"PDF text extraction failed: {e}"
            raise RuntimeError(msg) from e

        full_text = "\n".join(text_parts).strip()
        return ExtractionResult(full_text, metadata)

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle PDF content."""
        return content_type == ContentType.PDF

    async def _ocr_page(self, page: object) -> str:
        """Perform OCR on a PDF page."""
        try:
            pix = page.get_pixmap(dpi=self.ocr_dpi)  # type: ignore[misc]
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)  # type: ignore[misc]
            return str(pytesseract.image_to_string(img))  # type: ignore[misc]
        except (ValueError, OSError, pytesseract.TesseractError):  # type: ignore[misc]
            return ""
