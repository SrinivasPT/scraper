"""Comprehensive tests for regscraper_v2 architecture."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from regscraper_v2.interfaces import (
    DownloadResult,
    ExtractionResult,
    ContentType,
    Document,
)
from regscraper_v2.infrastructure.compliance import (
    RobotsTxtChecker,
    DomainThrottler,
    ThrottledRobotsChecker,
)
from regscraper_v2.downloaders.implementations import (
    HttpDownloader,
    PlaywrightDownloader,
)
from regscraper_v2.downloaders.factory import DownloaderFactory
from regscraper_v2.extractors.implementations import (
    PdfTextExtractor,
    DocxTextExtractor,
    HtmlTextExtractor,
)
from regscraper_v2.extractors.factory import ExtractorFactory


class TestInterfaces:
    """Test the core data structures and interfaces."""

    def test_download_result_creation(self):
        """Test DownloadResult data structure."""
        content = b"test content"
        result = DownloadResult(
            content, "application/pdf", "https://example.com/test.pdf"
        )

        assert result.content == content
        assert result.content_type == "application/pdf"
        assert result.url == "https://example.com/test.pdf"
        assert result.size == len(content)

    def test_extraction_result_creation(self):
        """Test ExtractionResult data structure."""
        text = "extracted text content"
        metadata = {"pages": 5}
        result = ExtractionResult(text, metadata)

        assert result.text == text
        assert result.metadata == metadata
        assert result.length == len(text)

    def test_document_creation_and_serialization(self):
        """Test Document creation and serialization."""
        doc = Document(
            source_url="https://example.com/doc.pdf",
            title="Test Document",
            full_text="Document content here",
            publication_date="2025-01-01",
            document_type="regulation",
        )

        assert doc.source_url == "https://example.com/doc.pdf"
        assert doc.title == "Test Document"

        doc_dict = doc.to_dict()
        assert doc_dict["source_url"] == "https://example.com/doc.pdf"
        assert doc_dict["title"] == "Test Document"
        assert doc_dict["publication_date"] == "2025-01-01"


class TestRobotsTxtChecker:
    """Test robots.txt compliance checking."""

    @pytest.mark.asyncio
    async def test_robots_allowed(self):
        """Test URL allowed by robots.txt."""
        checker = RobotsTxtChecker("TestBot/1.0")

        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful robots.txt response allowing all
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\\nAllow: /"

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await checker.is_allowed("https://example.com/test.pdf")
            assert result is True

    @pytest.mark.asyncio
    async def test_robots_disallowed(self):
        """Test URL disallowed by robots.txt."""
        checker = RobotsTxtChecker("TestBot/1.0")

        with patch("httpx.AsyncClient") as mock_client:
            # Mock robots.txt response disallowing all
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /"

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await checker.is_allowed("https://example.com/test.pdf")
            assert result is False

    @pytest.mark.asyncio
    async def test_robots_fetch_error_defaults_to_allow(self):
        """Test that robots.txt fetch errors default to allowing access."""
        checker = RobotsTxtChecker("TestBot/1.0")

        with patch("httpx.AsyncClient") as mock_client:
            # Mock network error
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = Exception("Network error")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await checker.is_allowed("https://example.com/test.pdf")
            assert result is True  # Should default to allowing

    def test_crawl_delay_parsing(self):
        """Test crawl-delay parsing from robots.txt."""
        checker = RobotsTxtChecker("TestBot/1.0")

        # Test parsing crawl delay
        checker._parse_crawl_delay(
            "example.com", "User-agent: *\nCrawl-delay: 5\nAllow: /"
        )
        assert checker.get_crawl_delay("https://example.com/test") == 5.0

        # Test minimum crawl delay enforcement
        checker._parse_crawl_delay(
            "fast.com", "User-agent: *\nCrawl-delay: 0.1\nAllow: /"
        )
        assert (
            checker.get_crawl_delay("https://fast.com/test") == 0.5
        )  # Should be at least 0.5


class TestDomainThrottler:
    """Test domain-level throttling."""

    @pytest.mark.asyncio
    async def test_basic_throttling(self):
        """Test basic domain throttling functionality."""
        throttler = DomainThrottler(default_delay=0.1, default_concurrency=1)

        import time

        start_time = time.time()

        # First request should go through immediately
        await throttler.acquire("https://example.com/test1")
        throttler.release_global()

        # Second request should be delayed
        await throttler.acquire("https://example.com/test2")
        throttler.release_global()

        end_time = time.time()

        # Should take at least the delay time between requests to same domain
        total_time = end_time - start_time
        assert total_time >= 0.1  # At least one delay period

    def test_domain_configuration(self):
        """Test domain-specific configuration."""
        throttler = DomainThrottler()

        # Configure specific domain
        throttler.configure_domain("slow-site.com", delay=10.0, concurrency=1)

        # Verify domain lock was created
        domain_lock = throttler._get_domain_lock("slow-site.com")
        assert domain_lock._value == 1  # Concurrency of 1


class TestHttpDownloader:
    """Test HTTP downloader implementation."""

    @pytest.mark.asyncio
    async def test_successful_download(self):
        """Test successful HTTP download."""
        # Create mocks
        mock_compliance = AsyncMock()
        mock_compliance.check_and_acquire = AsyncMock()
        mock_compliance.release_throttle = Mock()

        downloader = HttpDownloader(mock_compliance)

        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.content = b"test pdf content"
            mock_response.headers = {"content-type": "application/pdf"}
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await downloader.download("https://example.com/test.pdf")

            assert isinstance(result, DownloadResult)
            assert result.content == b"test pdf content"
            assert result.content_type == "application/pdf"
            assert result.url == "https://example.com/test.pdf"

            # Verify compliance checking was called
            mock_compliance.check_and_acquire.assert_called_once_with(
                "https://example.com/test.pdf"
            )
            mock_compliance.release_throttle.assert_called_once()

    @pytest.mark.asyncio
    async def test_robots_blocked_download(self):
        """Test download blocked by robots.txt."""
        mock_compliance = AsyncMock()
        mock_compliance.check_and_acquire.side_effect = PermissionError(
            "Blocked by robots.txt"
        )

        downloader = HttpDownloader(mock_compliance)

        from tenacity import RetryError

        with pytest.raises(RetryError):
            await downloader.download("https://example.com/blocked.pdf")

    @pytest.mark.asyncio
    async def test_download_with_retry_on_failure(self):
        """Test download retry logic on HTTP errors."""
        mock_compliance = AsyncMock()
        mock_compliance.check_and_acquire = AsyncMock()
        mock_compliance.release_throttle = Mock()

        downloader = HttpDownloader(
            mock_compliance, timeout=1
        )  # Short timeout for testing

        with patch("httpx.AsyncClient") as mock_client:
            # Mock client that fails then succeeds
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = [
                Exception("Network error"),  # First attempt fails
                Exception("Network error"),  # Second attempt fails
                Exception("Network error"),  # Third attempt fails
            ]
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Should eventually fail after retries
            from tenacity import RetryError

            with pytest.raises(RetryError):
                await downloader.download("https://example.com/test.pdf")


class TestPdfTextExtractor:
    """Test PDF text extraction."""

    @pytest.mark.asyncio
    async def test_pdf_content_type_handling(self):
        """Test PDF extractor content type detection."""
        extractor = PdfTextExtractor()

        assert extractor.can_handle(ContentType.PDF) is True
        assert extractor.can_handle(ContentType.HTML) is False
        assert extractor.can_handle(ContentType.DOCX) is False

    @pytest.mark.asyncio
    async def test_pdf_text_extraction_success(self):
        """Test successful PDF text extraction."""
        extractor = PdfTextExtractor()
        download_result = DownloadResult(
            b"fake pdf content", "application/pdf", "https://example.com/test.pdf"
        )

        with patch("fitz.open") as mock_fitz_open:
            # Mock PDF document with extractable text
            mock_page = Mock()
            mock_page.get_text.return_value = "Extracted PDF text content"

            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.close = Mock()

            mock_fitz_open.return_value = mock_doc

            result = await extractor.extract(download_result)

            assert isinstance(result, ExtractionResult)
            assert result.text == "Extracted PDF text content"
            assert result.metadata["pages_processed"] == 1
            assert result.metadata["ocr_pages"] == 0

            mock_doc.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_pdf_ocr_fallback(self):
        """Test PDF OCR fallback when no direct text available."""
        extractor = PdfTextExtractor()
        download_result = DownloadResult(
            b"fake pdf content", "application/pdf", "https://example.com/test.pdf"
        )

        with patch("fitz.open") as mock_fitz_open, patch.object(
            extractor, "_ocr_page", return_value="OCR extracted text"
        ) as mock_ocr:

            # Mock PDF page with no direct text (image-based)
            mock_page = Mock()
            mock_page.get_text.return_value = ""  # No direct text

            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.close = Mock()

            mock_fitz_open.return_value = mock_doc

            result = await extractor.extract(download_result)

            assert result.text == "OCR extracted text"
            assert result.metadata["ocr_pages"] == 1
            mock_ocr.assert_called_once_with(mock_page)


class TestDocxTextExtractor:
    """Test DOCX text extraction."""

    @pytest.mark.asyncio
    async def test_docx_content_type_handling(self):
        """Test DOCX extractor content type detection."""
        extractor = DocxTextExtractor()

        assert extractor.can_handle(ContentType.DOCX) is True
        assert extractor.can_handle(ContentType.PDF) is False
        assert extractor.can_handle(ContentType.HTML) is False

    @pytest.mark.asyncio
    async def test_docx_text_extraction(self):
        """Test DOCX text extraction."""
        extractor = DocxTextExtractor()
        download_result = DownloadResult(
            b"fake docx content",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "https://example.com/test.docx",
        )

        with patch(
            "regscraper_v2.extractors.implementations.DocxDocument"
        ) as mock_docx:
            # Mock DOCX document with paragraphs
            mock_paragraph1 = Mock()
            mock_paragraph1.text = "First paragraph"
            mock_paragraph2 = Mock()
            mock_paragraph2.text = "Second paragraph"

            mock_doc = Mock()
            mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
            mock_docx.return_value = mock_doc

            result = await extractor.extract(download_result)

            assert isinstance(result, ExtractionResult)
            assert result.text == "First paragraph\\nSecond paragraph"
            assert result.metadata["format"] == "docx"
            assert result.metadata["paragraphs"] == 2

    @pytest.mark.asyncio
    async def test_doc_legacy_format_detection(self):
        """Test legacy DOC format detection and handling."""
        extractor = DocxTextExtractor()

        # Test URL-based detection
        download_result = DownloadResult(
            b"fake doc content", "application/msword", "https://example.com/test.doc"
        )

        with patch("mammoth.extract_raw_text") as mock_mammoth:
            mock_result = Mock()
            mock_result.value = "Legacy DOC text content"
            mock_result.messages = []
            mock_mammoth.return_value = mock_result

            result = await extractor.extract(download_result)

            assert result.text == "Legacy DOC text content"
            assert result.metadata["format"] == "doc"


class TestHtmlTextExtractor:
    """Test HTML text extraction."""

    @pytest.mark.asyncio
    async def test_html_content_type_handling(self):
        """Test HTML extractor content type detection."""
        extractor = HtmlTextExtractor()

        assert extractor.can_handle(ContentType.HTML) is True
        assert extractor.can_handle(ContentType.PDF) is False

    @pytest.mark.asyncio
    async def test_html_text_extraction_trafilatura(self):
        """Test HTML text extraction using trafilatura."""
        extractor = HtmlTextExtractor()
        html_content = (
            "<html><body><h1>Title</h1><p>Content paragraph</p></body></html>"
        )
        download_result = DownloadResult(
            html_content.encode(), "text/html", "https://example.com/page.html"
        )

        with patch(
            "trafilatura.extract", return_value="Title\\nContent paragraph"
        ) as mock_trafilatura:
            result = await extractor.extract(download_result)

            assert result.text == "Title\\nContent paragraph"
            assert result.metadata["extraction_method"] == "trafilatura"
            mock_trafilatura.assert_called_once()

    @pytest.mark.asyncio
    async def test_html_text_extraction_fallback(self):
        """Test HTML text extraction fallback when trafilatura fails."""
        extractor = HtmlTextExtractor()
        html_content = "<html><body><p>Simple content</p></body></html>"
        download_result = DownloadResult(
            html_content.encode(), "text/html", "https://example.com/page.html"
        )

        with patch("trafilatura.extract", return_value=None):  # Trafilatura fails
            result = await extractor.extract(download_result)

            # Should still extract some text using fallback method
            assert "Simple content" in result.text or result.text != ""
            assert result.metadata["extraction_method"] == "basic"


class TestFactories:
    """Test factory implementations."""

    def test_downloader_factory_static_site(self):
        """Test downloader factory creates HTTP downloader for static sites."""
        site_config = {"example.com": {"type": "static", "delay": 2.0}}
        factory = DownloaderFactory(site_config)

        downloader = factory.create_downloader("https://example.com/test.pdf")
        assert isinstance(downloader, HttpDownloader)

    def test_downloader_factory_dynamic_site(self):
        """Test downloader factory creates Playwright downloader for dynamic sites."""
        site_config = {"dynamic-site.com": {"type": "dynamic", "delay": 3.0}}
        factory = DownloaderFactory(site_config)

        downloader = factory.create_downloader("https://dynamic-site.com/test.html")
        assert isinstance(downloader, PlaywrightDownloader)

    def test_extractor_factory_pdf(self):
        """Test extractor factory creates PDF extractor for PDF URLs."""
        factory = ExtractorFactory()

        extractor = factory.create_extractor(
            "https://example.com/doc.pdf", "application/pdf"
        )
        assert isinstance(extractor, PdfTextExtractor)

    def test_extractor_factory_docx(self):
        """Test extractor factory creates DOCX extractor for DOCX URLs."""
        factory = ExtractorFactory()

        extractor = factory.create_extractor("https://example.com/doc.docx", "")
        assert isinstance(extractor, DocxTextExtractor)

        # Test DOC extension too
        extractor = factory.create_extractor("https://example.com/doc.doc", "")
        assert isinstance(extractor, DocxTextExtractor)

    def test_extractor_factory_html_default(self):
        """Test extractor factory defaults to HTML extractor for unknown types."""
        factory = ExtractorFactory()

        extractor = factory.create_extractor("https://example.com/page", "")
        assert isinstance(extractor, HtmlTextExtractor)

        # Test explicit HTML
        extractor = factory.create_extractor(
            "https://example.com/page.html", "text/html"
        )
        assert isinstance(extractor, HtmlTextExtractor)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
