"""Integration test to verify the refactored components work together."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from regscraper.parser.docx_v2 import download_and_extract_docx_v2
from regscraper.parser.pdf_v2 import download_and_extract_pdf_v2, extract_pdf_text


class TestIntegration:
    """Integration tests for refactored components."""

    @pytest.mark.asyncio
    async def test_pdf_v2_integration(self):
        """Test the complete PDF download and extraction flow."""
        test_content = b"fake pdf content"
        expected_text = "Extracted PDF text"

        with patch("regscraper.downloader.http_downloader.httpx.AsyncClient") as mock_client, patch("fitz.open") as mock_fitz_open:
            # Mock HTTP download
            mock_response = MagicMock()
            mock_response.content = test_content
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Mock PDF extraction
            mock_page = MagicMock()
            mock_page.get_text.return_value = expected_text

            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.close = MagicMock()

            mock_fitz_open.return_value = mock_doc

            # Test the integrated flow
            result = await download_and_extract_pdf_v2("https://example.com/test.pdf")

            assert result == expected_text
            mock_client_instance.get.assert_called_once()
            mock_doc.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_docx_v2_integration(self):
        """Test the complete DOCX download and extraction flow."""
        test_content = b"fake docx content"
        expected_text = "Extracted DOCX text"

        with (
            patch("regscraper.downloader.http_downloader.httpx.AsyncClient") as mock_client,
            patch("regscraper.extractors.docx_extractor.Document") as mock_document,
        ):
            # Mock HTTP download
            mock_response = MagicMock()
            mock_response.content = test_content
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Mock DOCX extraction
            mock_paragraph = MagicMock()
            mock_paragraph.text = expected_text

            mock_doc = MagicMock()
            mock_doc.paragraphs = [mock_paragraph]

            mock_document.return_value = mock_doc

            # Test the integrated flow
            result = await download_and_extract_docx_v2("https://example.com/test.docx")

            assert result == expected_text
            mock_client_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_separate_download_and_extraction(self):
        """Test that we can now download once and extract multiple times."""
        test_content = b"fake pdf content"
        expected_text = "Reusable PDF text"

        with patch("fitz.open") as mock_fitz_open:
            # Mock PDF extraction
            mock_page = MagicMock()
            mock_page.get_text.return_value = expected_text

            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.close = MagicMock()

            mock_fitz_open.return_value = mock_doc

            # Test that we can extract multiple times from the same content
            result1 = await extract_pdf_text(test_content)
            result2 = await extract_pdf_text(test_content)

            assert result1 == expected_text
            assert result2 == expected_text
            assert result1 == result2

            # Verify that the PDF was processed twice (two separate extractions)
            assert mock_fitz_open.call_count == 2
