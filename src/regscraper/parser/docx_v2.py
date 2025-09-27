"""New DOCX processing functions using separated download and extraction."""

from ..downloader.http_downloader import default_downloader
from ..extractors.docx_extractor import default_docx_extractor


async def download_and_extract_docx_v2(url: str) -> str:
    """Download DOCX/DOC from URL and extract text (new separated version)."""
    content = await default_downloader.download_file(url)
    is_doc_format = url.lower().endswith(".doc")
    return await default_docx_extractor.extract_text(
        content, is_doc_format=is_doc_format
    )


# Keep the old function as a wrapper for backward compatibility
async def download_and_extract_docx(url: str) -> str:
    """Download DOCX/DOC from URL and extract text (legacy wrapper)."""
    return await download_and_extract_docx_v2(url)


# New function for working with already downloaded content
async def extract_docx_text(content: bytes, is_doc_format: bool = False) -> str:
    """Extract text from DOCX/DOC content bytes."""
    return await default_docx_extractor.extract_text(
        content, is_doc_format=is_doc_format
    )
