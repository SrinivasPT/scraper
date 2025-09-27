"""PDF document processor implementation."""

from typing import Optional
from ..fetcher.session import HttpSession
from ..downloader.http_downloader import default_downloader
from ..extractors.pdf_extractor import default_pdf_extractor
from ..logging import logger
from .base import DocumentProcessor


class PdfProcessor(DocumentProcessor):
    """Processes PDF documents by downloading and extracting text."""

    async def process(self, session: HttpSession, url: str) -> Optional[str]:
        """Download PDF and extract text content."""
        try:
            logger.debug(f"Processing PDF: {url}")

            # Download PDF content
            content = await default_downloader.download_file(url)

            # Extract text
            text = await default_pdf_extractor.extract_text(content)

            if not text.strip():
                logger.warning(f"No text extracted from PDF: {url}")
                return None

            logger.debug(
                f"Successfully processed PDF: {len(text)} characters from {url}"
            )
            return text

        except Exception as e:
            logger.error(f"Error processing PDF {url}: {e}")
            return None

    def can_handle(self, url: str, content_type: Optional[str] = None) -> bool:
        """Check if URL points to a PDF file."""
        url_lower = url.lower()
        return url_lower.endswith(".pdf") or (
            content_type and "pdf" in content_type.lower()
        )

    def get_processor_type(self) -> str:
        """Return processor type identifier."""
        return "pdf"
