"""Base text extractor interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class TextExtractor(ABC):
    """Abstract base class for text extraction from different file formats."""

    @abstractmethod
    async def extract_text(self, content: bytes | BinaryIO) -> str:
        """Extract text from binary content or stream."""
        pass

    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """Check if this extractor supports the given file format."""
        pass
