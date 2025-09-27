"""Tests for the new separated download and extraction functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from regscraper.downloader.http_downloader import HttpDownloader
from regscraper.extractors.pdf_extractor import PdfExtractor
from regscraper.extractors.docx_extractor import DocxExtractor


class TestHttpDownloader:
    """Test the HTTP downloader component."""

    @pytest.mark.asyncio
    async def test_download_file_success(self):
        """Test successful file download."""
        downloader = HttpDownloader(timeout=10)
        test_content = b"test file content"

        with patch("httpx.AsyncClient") as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.content = test_content
            mock_response.raise_for_status = MagicMock()

            # Setup mock client context manager
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Test download
            result = await downloader.download_file("https://example.com/test.pdf")

            assert result == test_content
            mock_client_instance.get.assert_called_once_with(
                "https://example.com/test.pdf"
            )

    @pytest.mark.asyncio
    async def test_download_to_stream(self):
        """Test downloading to BytesIO stream."""
        downloader = HttpDownloader()
        test_content = b"stream test content"

        with patch.object(downloader, "download_file", return_value=test_content):
            stream = await downloader.download_to_stream("https://example.com/test.pdf")

            assert stream.read() == test_content
            # Reset stream position and read again to verify it works
            stream.seek(0)
            assert stream.read() == test_content


class TestPdfExtractor:
    """Test the PDF text extractor component."""

    @pytest.mark.asyncio
    async def test_supports_format(self):
        """Test format support detection."""
        extractor = PdfExtractor()

        assert extractor.supports_format(".pdf") is True
        assert extractor.supports_format(".PDF") is True
        assert extractor.supports_format(".docx") is False
        assert extractor.supports_format(".txt") is False

    @pytest.mark.asyncio
    async def test_extract_text_with_mock_pdf(self):
        """Test text extraction with mocked PDF."""
        extractor = PdfExtractor()
        test_content = b"fake pdf content"
        expected_text = "Extracted text from PDF"

        with patch("fitz.open") as mock_fitz_open:
            # Setup mock PDF document
            mock_page = MagicMock()
            mock_page.get_text.return_value = expected_text

            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.close = MagicMock()

            mock_fitz_open.return_value = mock_doc

            # Test extraction
            result = await extractor.extract_text(test_content)

            assert result == expected_text
            mock_doc.close.assert_called_once()


class TestDocxExtractor:
    """Test the DOCX text extractor component."""

    @pytest.mark.asyncio
    async def test_supports_format(self):
        """Test format support detection."""
        extractor = DocxExtractor()

        assert extractor.supports_format(".docx") is True
        assert extractor.supports_format(".doc") is True
        assert extractor.supports_format(".DOCX") is True
        assert extractor.supports_format(".pdf") is False

    @pytest.mark.asyncio
    async def test_extract_docx_text(self):
        """Test DOCX text extraction."""
        extractor = DocxExtractor()
        test_content = b"fake docx content"
        expected_text = "Test paragraph"

        with patch("regscraper.extractors.docx_extractor.Document") as mock_document:
            # Setup mock paragraph
            mock_paragraph = MagicMock()
            mock_paragraph.text = expected_text

            mock_doc = MagicMock()
            mock_doc.paragraphs = [mock_paragraph]

            mock_document.return_value = mock_doc

            # Test extraction
            result = await extractor.extract_text(test_content, is_doc_format=False)

            assert result == expected_text

    @pytest.mark.asyncio
    async def test_extract_doc_text(self):
        """Test DOC text extraction using mammoth."""
        extractor = DocxExtractor()
        test_content = b"fake doc content"
        expected_text = "Text from DOC file"

        with patch("mammoth.extract_raw_text") as mock_mammoth:
            # Setup mock mammoth result
            mock_result = MagicMock()
            mock_result.value = expected_text
            mock_result.messages = []

            mock_mammoth.return_value = mock_result

            # Test extraction
            result = await extractor.extract_text(test_content, is_doc_format=True)

            assert result == expected_text
