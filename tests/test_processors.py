"""Tests for the new processor strategy pattern."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from regscraper.processors.docx_processor import DocxProcessor
from regscraper.processors.factory import ProcessorFactory
from regscraper.processors.html_processor import HtmlProcessor
from regscraper.processors.pdf_processor import PdfProcessor
from regscraper.processors.rss_processor import RssProcessor


class TestProcessorFactory:
    """Test the processor factory."""

    def test_pdf_processor_selection(self):
        """Test that PDF URLs select the PDF processor."""
        factory = ProcessorFactory()
        processor = factory.get_processor("https://example.com/document.pdf")
        assert isinstance(processor, PdfProcessor)
        assert processor.get_processor_type() == "pdf"

    def test_docx_processor_selection(self):
        """Test that DOCX URLs select the DOCX processor."""
        factory = ProcessorFactory()
        processor = factory.get_processor("https://example.com/document.docx")
        assert isinstance(processor, DocxProcessor)
        assert processor.get_processor_type() == "docx"

    def test_doc_processor_selection(self):
        """Test that DOC URLs select the DOCX processor."""
        factory = ProcessorFactory()
        processor = factory.get_processor("https://example.com/document.doc")
        assert isinstance(processor, DocxProcessor)
        assert processor.get_processor_type() == "docx"

    def test_rss_processor_selection(self):
        """Test that RSS URLs select the RSS processor."""
        factory = ProcessorFactory()
        processor = factory.get_processor("https://example.com/feed.rss")
        assert isinstance(processor, RssProcessor)
        assert processor.get_processor_type() == "rss"

        processor = factory.get_processor("https://example.com/news/feed")
        assert isinstance(processor, RssProcessor)

    def test_html_processor_fallback(self):
        """Test that unknown URLs fall back to HTML processor."""
        factory = ProcessorFactory()
        processor = factory.get_processor("https://example.com/page.html")
        assert isinstance(processor, HtmlProcessor)
        assert processor.get_processor_type() == "html"

        # Test generic URL
        processor = factory.get_processor("https://example.com/some-page")
        assert isinstance(processor, HtmlProcessor)

    def test_content_type_handling(self):
        """Test processor selection with content type."""
        factory = ProcessorFactory()

        # PDF content type
        processor = factory.get_processor("https://example.com/file", "application/pdf")
        assert isinstance(processor, PdfProcessor)

        # DOCX content type
        processor = factory.get_processor(
            "https://example.com/file",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert isinstance(processor, DocxProcessor)

        # HTML content type
        processor = factory.get_processor("https://example.com/file", "text/html")
        assert isinstance(processor, HtmlProcessor)


class TestPdfProcessor:
    """Test the PDF processor."""

    @pytest.mark.asyncio
    async def test_can_handle_pdf_urls(self):
        """Test PDF processor URL recognition."""
        processor = PdfProcessor()

        assert processor.can_handle("https://example.com/doc.pdf") is True
        assert processor.can_handle("https://example.com/doc.PDF") is True
        assert processor.can_handle("https://example.com/doc.html") is False
        assert processor.can_handle("https://example.com/doc", "application/pdf") is True

    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful PDF processing."""
        processor = PdfProcessor()
        mock_session = MagicMock()

        with (
            patch("regscraper.processors.pdf_processor.default_downloader") as mock_downloader,
            patch("regscraper.processors.pdf_processor.default_pdf_extractor") as mock_extractor,
        ):
            # Set up async mocks
            mock_downloader.download_file = AsyncMock(return_value=b"fake pdf content")
            mock_extractor.extract_text = AsyncMock(return_value="Extracted PDF text")

            result = await processor.process(mock_session, "https://example.com/test.pdf")

            assert result == "Extracted PDF text"
            mock_downloader.download_file.assert_called_once_with("https://example.com/test.pdf")
            mock_extractor.extract_text.assert_called_once_with(b"fake pdf content")


class TestDocxProcessor:
    """Test the DOCX processor."""

    @pytest.mark.asyncio
    async def test_can_handle_docx_urls(self):
        """Test DOCX processor URL recognition."""
        processor = DocxProcessor()

        assert processor.can_handle("https://example.com/doc.docx") is True
        assert processor.can_handle("https://example.com/doc.doc") is True
        assert processor.can_handle("https://example.com/doc.pdf") is False
        assert (
            processor.can_handle(
                "https://example.com/doc",
                "application/vnd.openxmlformats-officedocument",
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_process_docx_success(self):
        """Test successful DOCX processing."""
        processor = DocxProcessor()
        mock_session = MagicMock()

        with (
            patch("regscraper.processors.docx_processor.default_downloader") as mock_downloader,
            patch("regscraper.processors.docx_processor.default_docx_extractor") as mock_extractor,
        ):
            # Set up async mocks
            mock_downloader.download_file = AsyncMock(return_value=b"fake docx content")
            mock_extractor.extract_text = AsyncMock(return_value="Extracted DOCX text")

            result = await processor.process(mock_session, "https://example.com/test.docx")

            assert result == "Extracted DOCX text"
            mock_downloader.download_file.assert_called_once_with("https://example.com/test.docx")
            mock_extractor.extract_text.assert_called_once_with(b"fake docx content", is_doc_format=False)

    @pytest.mark.asyncio
    async def test_process_doc_success(self):
        """Test successful DOC processing."""
        processor = DocxProcessor()
        mock_session = MagicMock()

        with (
            patch("regscraper.processors.docx_processor.default_downloader") as mock_downloader,
            patch("regscraper.processors.docx_processor.default_docx_extractor") as mock_extractor,
        ):
            # Set up async mocks
            mock_downloader.download_file = AsyncMock(return_value=b"fake doc content")
            mock_extractor.extract_text = AsyncMock(return_value="Extracted DOC text")

            result = await processor.process(mock_session, "https://example.com/test.doc")

            assert result == "Extracted DOC text"
            mock_extractor.extract_text.assert_called_once_with(b"fake doc content", is_doc_format=True)


class TestHtmlProcessor:
    """Test the HTML processor."""

    @pytest.mark.asyncio
    async def test_can_handle_html_urls(self):
        """Test HTML processor URL recognition."""
        processor = HtmlProcessor()

        assert processor.can_handle("https://example.com/page.html") is True
        assert processor.can_handle("https://example.com/page") is True
        assert processor.can_handle("https://example.com/doc.pdf") is False
        assert processor.can_handle("https://example.com/feed") is False

    @pytest.mark.asyncio
    async def test_process_static_success(self):
        """Test successful static HTML processing."""
        processor = HtmlProcessor()
        mock_session = MagicMock()

        with (
            patch("regscraper.processors.html_processor.fetch_html") as mock_fetch,
            patch("regscraper.processors.html_processor.extract_clean_text") as mock_extract,
            patch("regscraper.processors.html_processor.settings") as mock_settings,
        ):
            mock_settings.site_overrides = {}
            mock_fetch.return_value = "<html><body>Test HTML</body></html>"
            mock_extract.return_value = "Test HTML content"

            result = await processor.process(mock_session, "https://example.com/page.html")

            assert result == "Test HTML content"
            mock_fetch.assert_called_once_with(mock_session, "https://example.com/page.html")


class TestRssProcessor:
    """Test the RSS processor."""

    @pytest.mark.asyncio
    async def test_can_handle_rss_urls(self):
        """Test RSS processor URL recognition."""
        processor = RssProcessor()

        assert processor.can_handle("https://example.com/feed.rss") is True
        assert processor.can_handle("https://example.com/news/feed") is True
        assert processor.can_handle("https://example.com/page.html") is False
        assert processor.can_handle("https://example.com/doc", "application/rss+xml") is True

    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful RSS processing."""
        processor = RssProcessor()
        mock_session = MagicMock()

        mock_rss_items = [
            {
                "title": "Test Article",
                "summary": "Test summary",
                "link": "https://example.com/article1",
            },
            {
                "title": "Another Article",
                "summary": "Another summary",
                "link": "https://example.com/article2",
            },
        ]

        with (
            patch("regscraper.processors.rss_processor.fetch_and_parse_rss") as mock_fetch,
            patch("regscraper.processors.rss_processor.extract_with_llm") as mock_llm,
        ):
            mock_fetch.return_value = mock_rss_items
            mock_llm.side_effect = [
                {
                    "title": "Test Article",
                    "source_url": "https://example.com/article1",
                    "full_text": "content1",
                },
                {
                    "title": "Another Article",
                    "source_url": "https://example.com/article2",
                    "full_text": "content2",
                },
            ]

            result = await processor.process(mock_session, "https://example.com/feed.rss")

            assert isinstance(result, dict)
            assert "items" in result
            assert len(result["items"]) == 2
            assert result["items"][0]["title"] == "Test Article"
