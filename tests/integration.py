"""Integration tests for async downloading and processing."""

import asyncio
import logging
import time
from contextlib import redirect_stdout
from io import StringIO

import pytest

from regscraper.__main__ import scrape_url
from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory

logger = logging.getLogger(__name__)


class TestAsyncDownloading:
    """Integration tests for async downloads with SEC URLs."""

    @pytest.fixture
    def sec_urls(self) -> list[str]:
        """Valid SEC press release URLs for testing."""
        return [
            "https://www.sec.gov/newsroom/press-releases/2025-126-sec-seeks-public-comment-improve-rules-residential-mortgage-backed-securities-asset-backed",
            "https://www.sec.gov/newsroom/press-releases/2025-125-sec-announces-departure-chief-operating-officer-ken-johnson",
            "https://www.sec.gov/newsroom/press-releases/2025-124-sec-announces-agenda-panelists-sec-cftc-roundtable-regulatory-harmonization-efforts",
        ]

    @pytest.mark.asyncio
    async def test_async_sec_downloads(self, sec_urls: list[str]) -> None:
        """Test async downloads of SEC URLs to verify rate limiting."""
        logger.info("🔄 Starting async SEC downloads test")

        # Create factories with SEC-specific throttling (same as scrape_url)
        downloader_factory = DownloaderFactory(
            site_overrides={"sec.gov": {"delay": 2.0, "concurrency": 1, "type": "static"}},
            default_delay=2.0,
            default_concurrency=1,
            user_agent="RegScraper/2.0 (Test)",
        )
        extractor_factory = ExtractorFactory()

        async def process_url(url: str) -> tuple[str, bool, int]:
            """Process a single URL and return result info."""
            logger.info("⬇️  Processing: %s", url)

            start_time = time.time()

            # Create downloaders and extractors
            downloader = downloader_factory.create_downloader(url)
            extractor = extractor_factory.create_extractor(url)

            # Download
            download_result = await downloader.download(url)
            logger.info("✅ Downloaded %s bytes from %s", len(download_result.content), url)

            # Extract
            extraction_result = await extractor.extract(download_result)
            processing_time = time.time() - start_time

            logger.info("✅ Extracted %s chars in %.2fs", len(extraction_result.text), processing_time)

            return url, True, len(extraction_result.text)

        # Run all downloads concurrently
        start_time = time.time()
        results = await asyncio.gather(*[process_url(url) for url in sec_urls], return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if isinstance(r, tuple) and r[1]]

        logger.info("📊 Factory approach completed in %.2fs", total_time)
        logger.info("📊 Success rate: %d/%d URLs", len(successful), len(sec_urls))

        # Assertions
        assert len(successful) >= 2, f"Expected at least 2 successes, got {len(successful)}"
        assert total_time >= 3.0, f"Downloads too fast ({total_time:.2f}s), throttling not working"
        assert total_time <= 30.0, f"Downloads too slow ({total_time:.2f}s), may have issues"

    @pytest.mark.asyncio
    async def test_async_sec_downloads_using_scrape_url(self, sec_urls: list[str]) -> None:
        """Test async downloads using the main scrape_url function."""
        logger.info("🔄 Starting scrape_url test")

        async def scrape_with_capture(url: str) -> tuple[str, bool, str]:
            """Scrape URL with stdout capture."""
            logger.info("⬇️  Scraping: %s", url)

            # Capture stdout from scrape_url
            output = StringIO()
            try:
                with redirect_stdout(output):
                    await scrape_url(url)
            except (ConnectionError, TimeoutError, ValueError) as e:
                logger.info("❌ Scrape failed for %s: %s", url, e)
                return url, False, str(e)
            else:
                output_str = output.getvalue()
                logger.info("✅ Scraped successfully: %s", url)
                return url, True, output_str

        # Run all scrapes concurrently
        start_time = time.time()
        results = await asyncio.gather(*[scrape_with_capture(url) for url in sec_urls], return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if isinstance(r, tuple) and r[1]]

        logger.info("📊 scrape_url approach completed in %.2fs", total_time)
        logger.info("📊 Success rate: %d/%d URLs", len(successful), len(sec_urls))

        # Validate content was captured
        for result in successful:
            url, success, content = result
            if success and content:
                logger.info("📄 Captured content from %s: %d chars", url, len(content))
                assert len(content) > 100, f"Too little content from {url}"

        # Assertions
        # Note: scrape_url creates independent throttlers per call, so concurrent
        # calls don't share throttling state like the factory approach does
        assert len(successful) >= 2, f"Expected at least 2 successes with scrape_url, got {len(successful)}"
        assert total_time >= 1.0, f"scrape_url too fast ({total_time:.2f}s), basic sanity check failed"
        assert total_time <= 25.0, f"scrape_url too slow ({total_time:.2f}s), may have issues"
