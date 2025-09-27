import trafilatura

from regscraper.interfaces import ContentType, DownloadResult, ExtractionResult, TextExtractor


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
            msg = f"HTML text extraction failed: {e}"
            raise RuntimeError(msg)

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
