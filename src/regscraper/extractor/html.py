from __future__ import annotations

import re

import trafilatura

from regscraper.interfaces import ContentType, DownloadResult, ExtractionResult, TextExtractor

# Try to import BeautifulSoup - it's optional
try:
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]

    _has_beautifulsoup = True
except ImportError:
    BeautifulSoup = None  # type: ignore[misc,assignment]
    _has_beautifulsoup = False


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

            metadata: dict[str, int | str] = {
                "original_length": len(html_content),
                "extraction_method": extraction_method,
            }

            return ExtractionResult(extracted_text or "", metadata)

        except (UnicodeDecodeError, ValueError) as e:
            msg = f"HTML text extraction failed: {e}"
            raise RuntimeError(msg) from e

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle HTML content."""
        return content_type == ContentType.HTML

    def _basic_html_extraction(self, html_content: str) -> str:
        """Basic HTML text extraction as fallback."""
        if _has_beautifulsoup:
            soup = BeautifulSoup(html_content, "html.parser")  # type: ignore[misc]

            # Remove script and style elements
            for element in soup(["script", "style"]):  # type: ignore[misc]
                element.decompose()  # type: ignore[misc]

            return soup.get_text(separator="\n", strip=True)  # type: ignore[misc]

        # If BeautifulSoup is not available, use regex extraction
        return self._regex_html_extraction(html_content)

    def _regex_html_extraction(self, html_content: str) -> str:
        """Very basic HTML text extraction using regex."""
        # Remove HTML tags (very basic approach)
        clean_text = re.sub(r"<[^>]+>", " ", html_content)
        # Clean up whitespace
        clean_text = re.sub(r"\s+", " ", clean_text)
        return clean_text.strip()
