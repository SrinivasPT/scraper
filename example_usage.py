#!/usr/bin/env python3
"""Example usage of the regscraper library."""

import asyncio
import logging
from typing import Any

# Import the main components from the new v2 architecture
from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory
from regscraper.infrastructure import DomainThrottler, RobotsTxtChecker, ThrottledRobotsChecker
from regscraper.interfaces import ExtractionResult

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main() -> ExtractionResult | None:
    """Demonstrate how to use regscraper as a library."""
    # Example URL to process
    url = "https://www.sec.gov/files/rules/concept/2025/33-11391.pdf"

    logger.info("Processing URL: %s", url)

    try:
        # Set up the infrastructure components
        robots_checker = RobotsTxtChecker("RegScraper/2.0")
        throttler = DomainThrottler(default_delay=2.0)
        compliance = ThrottledRobotsChecker(robots_checker, throttler)

        # Create factory for downloaders
        site_overrides: dict[str, dict[str, Any]] = {"sec.gov": {"delay": 5.0, "concurrency": 1, "type": "static"}}
        downloader_factory = DownloaderFactory(site_overrides)

        # Create downloader and extractor
        downloader = downloader_factory.create_downloader(url)
        extractor_factory = ExtractorFactory()

        # Download the content
        logger.info("📥 Downloading content...")
        download_result = await downloader.download(url)
        logger.info("✅ Downloaded %d bytes", len(download_result.content))
        logger.info("   Content type: %s", download_result.content_type)

        # Extract text from the downloaded content
        content_type = download_result.content_type or ""
        extractor = extractor_factory.create_extractor(url, content_type)
        logger.info("📝 Extracting text...")
        extraction_result = await extractor.extract(download_result)

        # Display results
        text_preview = extraction_result.text[:500] + "..." if len(extraction_result.text) > 500 else extraction_result.text
        logger.info("✅ Extracted %d characters", len(extraction_result.text))
        logger.info("   Metadata keys: %s", list(extraction_result.metadata.keys()))
        logger.info("   Preview: %s", text_preview)

    except (ValueError, RuntimeError, PermissionError):
        logger.exception("❌ Error occurred")
        return None
    else:
        return extraction_result


if __name__ == "__main__":
    asyncio.run(main())
