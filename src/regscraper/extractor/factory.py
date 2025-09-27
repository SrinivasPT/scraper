from __future__ import annotations

from regscraper.interfaces import ContentType, TextExtractor

from .docx import DocxTextExtractor
from .html import HtmlTextExtractor
from .pdf import PdfTextExtractor


class ExtractorFactory:
    """Factory for creating text extractors based on content type."""

    def __init__(self) -> None:
        self._extractors: dict[ContentType, TextExtractor] = {
            ContentType.PDF: PdfTextExtractor(),
            ContentType.DOCX: DocxTextExtractor(),
            ContentType.HTML: HtmlTextExtractor(),
        }

    def create_extractor(self, url: str, content_type: str = "") -> TextExtractor:
        """Create appropriate extractor based on URL and content type."""
        detected_type = self._detect_content_type(url, content_type)

        if detected_type in self._extractors:
            return self._extractors[detected_type]

        # Default to HTML extractor for unknown types
        return self._extractors[ContentType.HTML]

    def _detect_content_type(self, url: str, content_type: str) -> ContentType:
        """Detect content type from URL and HTTP content-type header."""
        # First, try to detect from URL extension
        url_lower = url.lower()

        if url_lower.endswith(".pdf"):
            return ContentType.PDF
        if url_lower.endswith((".docx", ".doc")):
            return ContentType.DOCX
        if any(indicator in url_lower for indicator in [".rss", "/feed", "/rss"]):
            return ContentType.RSS

        # Then try HTTP content-type header
        if content_type:
            content_type_lower = content_type.lower()

            if "pdf" in content_type_lower:
                return ContentType.PDF
            if any(doc_type in content_type_lower for doc_type in ["msword", "wordprocessingml"]):
                return ContentType.DOCX
            if any(rss_type in content_type_lower for rss_type in ["rss", "xml", "atom"]):
                return ContentType.RSS
            if "html" in content_type_lower:
                return ContentType.HTML

        # Default to HTML for ambiguous cases
        return ContentType.HTML

    def register_extractor(self, content_type: ContentType, extractor: TextExtractor) -> None:
        """Register a custom extractor for a content type."""
        self._extractors[content_type] = extractor
