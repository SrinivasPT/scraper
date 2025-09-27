"""Base document processor interface using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Optional
from ..fetcher.session import HttpSession


class DocumentProcessor(ABC):
    """Abstract base class for document processing strategies."""

    @abstractmethod
    async def process(self, session: HttpSession, url: str) -> Optional[str]:
        """Process a document URL and return extracted text."""
        pass

    @abstractmethod
    def can_handle(self, url: str, content_type: Optional[str] = None) -> bool:
        """Check if this processor can handle the given URL/content type."""
        pass

    @abstractmethod
    def get_processor_type(self) -> str:
        """Return the type of processor (for logging/debugging)."""
        pass
