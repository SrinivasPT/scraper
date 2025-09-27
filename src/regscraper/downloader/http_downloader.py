"""HTTP file downloader with proper error handling and retries."""

import io
from typing import BinaryIO
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from ..logging import logger


class HttpDownloader:
    """Handles HTTP file downloads with proper error handling."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def download_file(self, url: str) -> bytes:
        """Download a file from URL and return its content as bytes."""
        logger.debug(f"Downloading file from: {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            logger.debug(f"Downloaded {len(response.content)} bytes from {url}")
            return response.content

    async def download_to_stream(self, url: str) -> BinaryIO:
        """Download a file and return it as a BytesIO stream."""
        content = await self.download_file(url)
        return io.BytesIO(content)


# Default instance for convenience
default_downloader = HttpDownloader()
