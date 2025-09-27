"""Factory for creating appropriate document processors."""

from typing import List, Optional
from ..logging import logger
from .base import DocumentProcessor
from .pdf_processor import PdfProcessor
from .docx_processor import DocxProcessor
from .html_processor import HtmlProcessor
from .rss_processor import RssProcessor


class ProcessorFactory:
    """Factory class for creating and managing document processors."""

    def __init__(self):
        self._processors: List[DocumentProcessor] = [
            PdfProcessor(),
            DocxProcessor(),
            RssProcessor(),
            HtmlProcessor(),  # HTML should be last as it's the fallback
        ]

    def get_processor(
        self, url: str, content_type: Optional[str] = None
    ) -> DocumentProcessor:
        """Get the appropriate processor for a given URL and content type."""
        for processor in self._processors:
            if processor.can_handle(url, content_type):
                logger.debug(
                    f"Selected {processor.get_processor_type()} processor for {url}"
                )
                return processor

        # Fallback to HTML processor (should never happen as HTML handles everything)
        logger.warning(f"No specific processor found for {url}, using HTML processor")
        return HtmlProcessor()

    def register_processor(self, processor: DocumentProcessor, priority: int = -1):
        """Register a new processor with optional priority (lower number = higher priority)."""
        if priority == -1:
            # Add at the end (before HTML fallback)
            self._processors.insert(-1, processor)
        else:
            self._processors.insert(priority, processor)

        logger.info(f"Registered {processor.get_processor_type()} processor")

    def list_processors(self) -> List[str]:
        """List all registered processor types."""
        return [p.get_processor_type() for p in self._processors]


# Global factory instance
processor_factory = ProcessorFactory()
