"""RSS document processor implementation."""

from typing import Optional, Dict, List
from ..parser.rss import fetch_and_parse_rss
from ..extractor.llm import extract_with_llm
from ..logging import logger
from .base import DocumentProcessor
from ..fetcher.session import HttpSession


class RssProcessor(DocumentProcessor):
    """Processes RSS feeds and extracts content from feed items."""

    async def process(
        self, session: HttpSession, url: str
    ) -> Optional[Dict[str, List[dict]]]:
        """Fetch RSS feed and process all items."""
        try:
            logger.debug(f"Processing RSS feed: {url}")

            # Fetch and parse RSS items
            items = await fetch_and_parse_rss(url)

            if not items:
                logger.warning(f"No items found in RSS feed: {url}")
                return None

            results: List[dict] = []

            # Process each RSS item
            for item in items:
                content = f"{item.get('title','')}\n\n{item.get('summary','')}"

                if content.strip():
                    # Extract structured data using LLM
                    doc = await extract_with_llm(content, item.get("link", url))
                    if doc:
                        results.append(doc)
                        logger.debug(
                            f"Processed RSS item: {item.get('title', 'Untitled')}"
                        )

            logger.info(
                f"Successfully processed RSS feed: {len(results)} items from {url}"
            )
            return {"items": results}

        except Exception as e:
            logger.error(f"Error processing RSS feed {url}: {e}")
            return None

    def can_handle(self, url: str, content_type: Optional[str] = None) -> bool:
        """Check if URL points to an RSS feed."""
        url_lower = url.lower()
        return (
            url_lower.endswith(".rss")
            or "/feed" in url_lower
            or ".rss" in url_lower
            or (
                content_type
                and any(fmt in content_type.lower() for fmt in ["rss", "xml", "atom"])
            )
        )

    def get_processor_type(self) -> str:
        """Return processor type identifier."""
        return "rss"
