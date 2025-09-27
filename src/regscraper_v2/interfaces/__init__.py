"""Core interfaces following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Optional, Protocol
from enum import Enum


class ContentType(Enum):
    """Supported content types."""

    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    RSS = "rss"


class DownloadResult:
    """Result of a download operation."""

    def __init__(
        self, content: bytes, content_type: Optional[str] = None, url: str = ""
    ):
        self.content = content
        self.content_type = content_type
        self.url = url
        self.size = len(content)


class ExtractionResult:
    """Result of text extraction."""

    def __init__(self, text: str, metadata: Optional[dict] = None):
        self.text = text
        self.metadata = metadata or {}
        self.length = len(text)


class Document:
    """Processed document with structured data."""

    def __init__(
        self,
        source_url: str,
        title: str,
        full_text: str,
        publication_date: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        document_type: str = "other",
        summary: Optional[str] = None,
    ):
        self.source_url = source_url
        self.title = title
        self.full_text = full_text
        self.publication_date = publication_date
        self.issuing_authority = issuing_authority
        self.document_type = document_type
        self.summary = summary

    def to_dict(self) -> dict:
        return {
            "source_url": self.source_url,
            "title": self.title,
            "full_text": self.full_text,
            "publication_date": self.publication_date,
            "issuing_authority": self.issuing_authority,
            "document_type": self.document_type,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Create Document from dictionary."""
        return cls(
            source_url=data["source_url"],
            title=data["title"],
            full_text=data["full_text"],
            publication_date=data["publication_date"],
            issuing_authority=data["issuing_authority"],
            document_type=data["document_type"],
            summary=data["summary"],
        )


# Core Interfaces (SOLID - Interface Segregation Principle)


class RobotsChecker(Protocol):
    """Interface for robots.txt compliance checking."""

    async def is_allowed(self, url: str) -> bool: ...


class Throttler(Protocol):
    """Interface for rate limiting."""

    async def acquire(self, url: str) -> None: ...


class Downloader(ABC):
    """Abstract base class for content downloading."""

    @abstractmethod
    async def download(self, url: str) -> DownloadResult:
        """Download content from URL."""
        pass


class TextExtractor(ABC):
    """Abstract base class for text extraction."""

    @abstractmethod
    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract text from downloaded content."""
        pass

    @abstractmethod
    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle the content type."""
        pass


class DocumentStructurer(Protocol):
    """Interface for structuring extracted text into documents."""

    async def structure(self, text: str, url: str) -> Document: ...


class DocumentStorage(ABC):
    """Abstract base class for document storage."""

    @abstractmethod
    async def store(self, document: Document) -> str:
        """Store document and return storage path/ID."""
        pass


class DocumentProcessor(ABC):
    """Abstract base class for complete document processing pipeline."""

    def __init__(
        self,
        downloader: Downloader,
        extractor: TextExtractor,
        structurer: DocumentStructurer,
        storage: DocumentStorage,
    ):
        self._downloader = downloader
        self._extractor = extractor
        self._structurer = structurer
        self._storage = storage

    async def process(self, url: str) -> Document:
        """Process a document through the complete pipeline."""
        # Template Method Pattern
        download_result = await self._download_step(url)
        extraction_result = await self._extract_step(download_result)
        document = await self._structure_step(extraction_result, url)
        await self._store_step(document)
        return document

    async def _download_step(self, url: str) -> DownloadResult:
        return await self._downloader.download(url)

    async def _extract_step(self, download_result: DownloadResult) -> ExtractionResult:
        return await self._extractor.extract(download_result)

    async def _structure_step(
        self, extraction_result: ExtractionResult, url: str
    ) -> Document:
        return await self._structurer.structure(extraction_result.text, url)

    async def _store_step(self, document: Document) -> str:
        return await self._storage.store(document)
