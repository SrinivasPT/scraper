"""Integration tests demonstrating the new regscraper_v2 architecture."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from regscraper_v2.downloaders.factory import DownloaderFactory
from regscraper_v2.downloaders.implementations import HttpDownloader
from regscraper_v2.extractors.factory import ExtractorFactory
from regscraper_v2.infrastructure.compliance import (
    DomainThrottler,
    RobotsTxtChecker,
    ThrottledRobotsChecker,
)
from regscraper_v2.interfaces import (
    ContentType,
    Document,
    DownloadResult,
    ExtractionResult,
)


class TestIntegrationScenarios:
    """Test complete workflows with the new architecture."""

    @pytest.mark.asyncio
    async def test_complete_pdf_processing_workflow(self):
        """Test end-to-end PDF document processing."""
        # Setup compliance infrastructure
        robots_checker = RobotsTxtChecker("TestBot/1.0")
        throttler = DomainThrottler(default_delay=0.1)  # Fast for testing
        compliance = ThrottledRobotsChecker(robots_checker, throttler)

        # Create downloader
        downloader = HttpDownloader(compliance)

        # Mock the download to return PDF content
        fake_pdf_content = b"fake pdf content"

        with patch.object(downloader, "download") as mock_download:
            mock_download.return_value = DownloadResult(fake_pdf_content, "application/pdf", "https://example.com/document.pdf")

            # Test download
            download_result = await downloader.download("https://example.com/document.pdf")
            assert download_result.content == fake_pdf_content
            assert download_result.content_type == "application/pdf"

            # Test extractor selection
            extractor_factory = ExtractorFactory()
            extractor = extractor_factory.create_extractor("https://example.com/document.pdf", "application/pdf")

            # Mock PDF extraction
            with patch("fitz.open") as mock_fitz:
                mock_page = Mock()
                mock_page.get_text.return_value = "Sample PDF content"

                mock_doc = Mock()
                mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
                mock_doc.close = Mock()

                mock_fitz.return_value = mock_doc

                # Extract text
                extraction_result = await extractor.extract(download_result)

                assert extraction_result.text == "Sample PDF content"
                assert extraction_result.metadata["pages_processed"] == 1

    @pytest.mark.asyncio
    async def test_downloader_factory_selection(self):
        """Test downloader factory selects appropriate downloader."""
        site_overrides = {}  # Empty site overrides for testing
        factory = DownloaderFactory(site_overrides)

        # Test static site selection (default)
        static_downloader = factory.create_downloader("https://example.com/static")
        assert isinstance(static_downloader, HttpDownloader)

        # Test dynamic site selection with site override
        site_overrides_dynamic = {"dynamic.example.com": {"type": "dynamic"}}
        factory_dynamic = DownloaderFactory(site_overrides_dynamic)

        with patch("regscraper_v2.downloaders.factory.PlaywrightDownloader") as MockPlaywright:
            factory_dynamic.create_downloader("https://dynamic.example.com/page")
            MockPlaywright.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_type_detection_and_extraction(self):
        """Test content type detection leads to correct extractor."""
        factory = ExtractorFactory()

        # Test PDF detection
        pdf_extractor = factory.create_extractor("https://example.com/doc.pdf", "application/pdf")
        assert pdf_extractor.can_handle(ContentType.PDF)

        # Test DOCX detection
        docx_extractor = factory.create_extractor(
            "https://example.com/doc.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert docx_extractor.can_handle(ContentType.DOCX)

        # Test HTML detection
        html_extractor = factory.create_extractor("https://example.com/page.html", "text/html")
        assert html_extractor.can_handle(ContentType.HTML)

    @pytest.mark.asyncio
    async def test_robots_txt_compliance_workflow(self):
        """Test robots.txt compliance checking workflow."""
        robots_checker = RobotsTxtChecker("TestBot/1.0")

        with patch("httpx.AsyncClient") as mock_client:
            # Mock robots.txt response that allows access
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nAllow: /documents/\nCrawl-delay: 1"

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Test that URL is allowed
            url = "https://example.com/documents/report.pdf"
            is_allowed = await robots_checker.is_allowed(url)
            assert is_allowed is True

            # Test crawl delay parsing
            delay = robots_checker.get_crawl_delay(url)
            assert delay == 1.0

    def test_document_metadata_structure(self):
        """Test document metadata structure and serialization."""
        # Create sample extraction result
        extraction_result = ExtractionResult(
            text="Sample extracted text",
            metadata={"pages": 5, "extraction_method": "direct", "format": "pdf"},
        )

        # Create document with metadata (using actual Document structure)
        document = Document(
            source_url="https://example.com/doc.pdf",
            title="Sample Document",
            full_text=extraction_result.text,
            publication_date="2024-01-01",
            issuing_authority="Test Authority",
            document_type="PDF Document",
            summary="A sample document for testing",
        )

        # Test serialization
        doc_dict = document.to_dict()
        assert doc_dict["source_url"] == "https://example.com/doc.pdf"
        assert doc_dict["full_text"] == "Sample extracted text"
        assert doc_dict["title"] == "Sample Document"

        # Test deserialization
        restored_doc = Document.from_dict(doc_dict)
        assert restored_doc.source_url == document.source_url
        assert restored_doc.full_text == document.full_text
        assert restored_doc.title == document.title

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms."""
        # Test HTML extraction with trafilatura failure
        from regscraper_v2.extractors.implementations import HtmlTextExtractor

        extractor = HtmlTextExtractor()
        html_content = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        download_result = DownloadResult(html_content.encode(), "text/html", "https://example.com/page.html")

        with patch("trafilatura.extract", return_value=None):  # Force fallback
            result = await extractor.extract(download_result)

            # Should still extract content using BeautifulSoup fallback
            assert "Title" in result.text
            assert "Content" in result.text
            assert result.metadata["extraction_method"] == "basic"


class TestArchitectureValidation:
    """Test that architecture follows SOLID principles."""

    def test_single_responsibility_principle(self):
        """Ensure each component has a single responsibility."""
        # Downloaders only download
        site_overrides = {}
        factory = DownloaderFactory(site_overrides)
        downloader = factory.create_downloader("https://example.com/static")

        # Should only have download-related methods, not extraction
        assert hasattr(downloader, "download")
        assert not hasattr(downloader, "extract_text")

        # Extractors only extract
        extractor_factory = ExtractorFactory()
        extractor = extractor_factory.create_extractor("test.pdf", "application/pdf")

        # Should only have extraction methods, not download
        assert hasattr(extractor, "extract")
        assert hasattr(extractor, "can_handle")
        assert not hasattr(extractor, "download")

    def test_open_closed_principle(self):
        """Test that components are open for extension, closed for modification."""
        # Can add new extractors without modifying existing ones
        from regscraper_v2.interfaces import TextExtractor

        class CustomExtractor(TextExtractor):
            """Custom extractor for demonstration."""

            async def extract(self, download_result):
                return ExtractionResult("custom text", {"method": "custom"})

            def can_handle(self, content_type):
                return content_type == ContentType.HTML  # Override for custom behavior

        # Should be able to instantiate and use
        custom_extractor = CustomExtractor()
        assert custom_extractor.can_handle(ContentType.HTML)

    def test_dependency_inversion_principle(self):
        """Test that high-level modules don't depend on low-level modules."""
        # HttpDownloader depends on abstract compliance checker interface
        compliance_mock = AsyncMock()  # Can be any implementation
        downloader = HttpDownloader(compliance_mock)

        # Downloader should work with any compliance implementation
        assert downloader._compliance_checker is compliance_mock

        # Factory can create different implementations
        site_overrides = {}
        factory = DownloaderFactory(site_overrides)
        downloader1 = factory.create_downloader("https://example.com/test1")
        downloader2 = factory.create_downloader("https://example.com/test2")

        # Different instances but same interface
        assert isinstance(downloader1, type(downloader2))
        assert downloader1 is not downloader2
