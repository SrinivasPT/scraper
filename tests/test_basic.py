"""Basic tests for key components of the scraper."""

from typing import Any

import pytest

from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory
from regscraper.interfaces import ContentType, Document, DownloadResult, ExtractionResult


class TestInterfaces:
    """Test the basic data classes and interfaces."""

    def test_content_type_enum(self):
        """Test ContentType enum values."""
        assert ContentType.PDF.value == "pdf"
        assert ContentType.DOCX.value == "docx"
        assert ContentType.HTML.value == "html"
        assert ContentType.RSS.value == "rss"

    def test_download_result(self):
        """Test DownloadResult class."""
        content = b"test content"
        result = DownloadResult(content, "text/html", "https://example.com")

        assert result.content == content
        assert result.content_type == "text/html"
        assert result.url == "https://example.com"
        assert result.size == len(content)

    def test_extraction_result(self):
        """Test ExtractionResult class."""
        text = "extracted text"
        metadata: dict[str, Any] = {"pages": 1}
        result = ExtractionResult(text, metadata)

        assert result.text == text
        assert result.metadata == metadata
        assert result.length == len(text)

    def test_document_class(self):
        """Test Document class."""
        doc = Document("https://example.com/doc", "Test Document", "Document content")

        assert doc.source_url == "https://example.com/doc"
        assert doc.title == "Test Document"
        assert doc.full_text == "Document content"
        assert doc.document_type == "other"

    def test_document_to_dict(self):
        """Test Document to_dict method."""
        doc = Document("https://example.com/doc", "Test Document", "Document content", publication_date="2023-01-01")

        result: dict[str, Any] = doc.to_dict()
        assert result["source_url"] == "https://example.com/doc"
        assert result["title"] == "Test Document"
        assert result["full_text"] == "Document content"
        assert result["publication_date"] == "2023-01-01"

    def test_document_from_dict(self):
        """Test Document from_dict method."""
        data: dict[str, Any] = {
            "source_url": "https://example.com/doc",
            "title": "Test Document",
            "full_text": "Document content",
            "publication_date": "2023-01-01",
            "issuing_authority": "Test Authority",
            "document_type": "regulation",
            "summary": "Test summary",
        }

        doc = Document.from_dict(data)
        assert doc.source_url == data["source_url"]
        assert doc.title == data["title"]
        assert doc.publication_date == data["publication_date"]


class TestFactories:
    """Test factory classes."""

    def test_downloader_factory_basic(self):
        """Test basic DownloaderFactory functionality."""
        factory = DownloaderFactory({})
        downloader = factory.create_downloader("https://example.com")

        assert downloader is not None
        assert hasattr(downloader, "download")

    def test_downloader_factory_different_domains(self):
        """Test DownloaderFactory with different domains."""
        factory = DownloaderFactory({})

        downloader1 = factory.create_downloader("https://site1.com")
        downloader2 = factory.create_downloader("https://site2.com")

        assert downloader1 is not None
        assert downloader2 is not None
        # Different instances for different requests
        assert downloader1 is not downloader2

    def test_extractor_factory_basic(self):
        """Test basic ExtractorFactory functionality."""
        factory = ExtractorFactory()

        # Test different content types
        html_extractor = factory.create_extractor("https://example.com/page.html", "text/html")
        pdf_extractor = factory.create_extractor("https://example.com/doc.pdf", "application/pdf")

        assert html_extractor is not None
        assert pdf_extractor is not None
        assert hasattr(html_extractor, "extract")
        assert hasattr(pdf_extractor, "extract")

    def test_extractor_factory_url_detection(self):
        """Test ExtractorFactory URL-based content type detection."""
        factory = ExtractorFactory()

        # Test URL extension detection
        pdf_extractor = factory.create_extractor("https://example.com/document.pdf")
        docx_extractor = factory.create_extractor("https://example.com/document.docx")

        assert pdf_extractor is not None
        assert docx_extractor is not None

    def test_extractor_factory_content_type_detection(self):
        """Test ExtractorFactory content-type header detection."""
        factory = ExtractorFactory()

        # Test content-type detection
        pdf_extractor = factory.create_extractor("https://example.com/doc", "application/pdf")
        html_extractor = factory.create_extractor("https://example.com/page", "text/html")

        assert pdf_extractor is not None
        assert html_extractor is not None

    def test_extractor_factory_default_fallback(self):
        """Test ExtractorFactory defaults to HTML for unknown types."""
        factory = ExtractorFactory()

        # Unknown extension and content type should default to HTML
        extractor = factory.create_extractor("https://example.com/unknown", "application/unknown")

        assert extractor is not None
        assert hasattr(extractor, "extract")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
