"""New PDF processing functions using separated download and extraction."""

from ..downloader.http_downloader import default_downloader
from ..extractors.pdf_extractor import default_pdf_extractor


async def download_and_extract_pdf_v2(url: str) -> str:
    """Download PDF from URL and extract text (new separated version)."""
    content = await default_downloader.download_file(url)
    return await default_pdf_extractor.extract_text(content)


# Keep the old function as a wrapper for backward compatibility
async def download_and_extract_pdf(url: str) -> str:
    """Download PDF from URL and extract text (legacy wrapper)."""
    return await download_and_extract_pdf_v2(url)


# New function for working with already downloaded content
async def extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF content bytes."""
    return await default_pdf_extractor.extract_text(content)
