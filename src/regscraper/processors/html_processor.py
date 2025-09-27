"""HTML document processor implementation."""

from typing import Optional
from ..fetcher.session import HttpSession
from ..fetcher.static import fetch_html
from ..fetcher.dynamic import fetch_dynamic_html
from ..parser.html import extract_clean_text
from ..config import settings
from ..utils.urls import domain_of
from ..logging import logger
from .base import DocumentProcessor


class HtmlProcessor(DocumentProcessor):
    """Processes HTML documents using static or dynamic fetching."""

    async def process(self, session: HttpSession, url: str) -> Optional[str]:
        """Fetch HTML and extract clean text content."""
        try:
            logger.debug(f"Processing HTML: {url}")

            # Check if site requires dynamic fetching
            domain = domain_of(url)
            site_config = settings.site_overrides.get(domain, {})
            fetch_type = site_config.get("type", "static")

            # Fetch HTML content
            if fetch_type == "dynamic":
                logger.debug(f"Using dynamic fetching for {url}")
                html = await fetch_dynamic_html(url)
            else:
                logger.debug(f"Using static fetching for {url}")
                html = await fetch_html(session, url)

            # Extract clean text
            text = extract_clean_text(html) or ""

            if not text.strip():
                logger.warning(f"No text extracted from HTML: {url}")
                return None

            logger.debug(
                f"Successfully processed HTML: {len(text)} characters from {url}"
            )
            return text

        except Exception as e:
            logger.error(f"Error processing HTML {url}: {e}")
            return None

    def can_handle(self, url: str, content_type: Optional[str] = None) -> bool:
        """Check if URL should be processed as HTML."""
        # HTML is the default/fallback processor
        url_lower = url.lower()

        # Not HTML if it's clearly another format
        if any(ext in url_lower for ext in [".pdf", ".docx", ".doc", ".rss", "/feed"]):
            return False

        # Check content type if available
        if content_type:
            content_lower = content_type.lower()
            return any(fmt in content_lower for fmt in ["html", "text/plain"])

        # Default to HTML for unknown types
        return True

    def get_processor_type(self) -> str:
        """Return processor type identifier."""
        return "html"
