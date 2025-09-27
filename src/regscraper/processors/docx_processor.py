"""DOCX document processor implementation."""

from typing import Optional
from ..fetcher.session import HttpSession
from ..downloader.http_downloader import default_downloader
from ..extractors.docx_extractor import default_docx_extractor
from ..logging import logger
from .base import DocumentProcessor


class DocxProcessor(DocumentProcessor):
    """Processes DOCX/DOC documents by downloading and extracting text."""

    async def process(self, session: HttpSession, url: str) -> Optional[str]:
        """Download DOCX/DOC and extract text content."""
        try:
            logger.debug(f"Processing DOCX/DOC: {url}")

            # Download document content
            content = await default_downloader.download_file(url)

            # Determine if it's a legacy DOC file
            is_doc_format = url.lower().endswith(".doc")

            # Extract text
            text = await default_docx_extractor.extract_text(
                content, is_doc_format=is_doc_format
            )

            if not text.strip():
                logger.warning(f"No text extracted from document: {url}")
                return None

            logger.debug(
                f"Successfully processed document: {len(text)} characters from {url}"
            )
            return text

        except Exception as e:
            logger.error(f"Error processing document {url}: {e}")
            return None

    def can_handle(self, url: str, content_type: Optional[str] = None) -> bool:
        """Check if URL points to a DOCX or DOC file."""
        url_lower = url.lower()
        return (
            url_lower.endswith(".docx")
            or url_lower.endswith(".doc")
            or (
                content_type
                and any(fmt in content_type.lower() for fmt in ["docx", "msword"])
            )
        )

    def get_processor_type(self) -> str:
        """Return processor type identifier."""
        return "docx"
