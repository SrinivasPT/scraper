#!/usr/bin/env python3
"""Main entry point for running regscraper as a module."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Import the main components
from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def scrape_url(
    url: str, output_format: str = "text", output_file: str | None = None, delay: float = 2.0, user_agent: str = "RegScraper/2.0"
) -> None:
    """Scrape a URL and extract its content."""
    try:
        # Create factories with SEC-specific throttling
        site_overrides: dict[str, dict[str, Any]] = {"sec.gov": {"delay": delay, "concurrency": 1, "type": "static"}}
        downloader_factory = DownloaderFactory(
            site_overrides=site_overrides, default_delay=delay, default_concurrency=1, user_agent=user_agent
        )
        extractor_factory = ExtractorFactory()

        # Download content
        logger.info("📥 Downloading: %s", url)
        downloader = downloader_factory.create_downloader(url)
        download_result = await downloader.download(url)

        logger.info("✅ Downloaded %d bytes (%s)", len(download_result.content), download_result.content_type)

        # Extract text
        logger.info("📝 Extracting text...")
        content_type = download_result.content_type or ""
        extractor = extractor_factory.create_extractor(url, content_type)
        extraction_result = await extractor.extract(download_result)

        logger.info("✅ Extracted %d characters", len(extraction_result.text))

        # Prepare output
        if output_format == "json":
            # Safely convert metadata to ensure JSON serialization
            metadata_dict: dict[str, Any] = {}
            try:
                # Use getattr to safely access metadata and convert to dict
                metadata = getattr(extraction_result, "metadata", {})
                if metadata:
                    # Use JSON serialization/deserialization to handle unknown types safely
                    metadata_json = json.dumps(metadata, default=str)
                    metadata_dict = json.loads(metadata_json)
            except (TypeError, ValueError, json.JSONDecodeError, AttributeError):
                metadata_dict = {"error": "metadata not available"}

            output_data: dict[str, Any] = {
                "url": url,
                "content_type": download_result.content_type,
                "text": extraction_result.text,
                "metadata": metadata_dict,
                "length": len(extraction_result.text),
            }
            output_content = json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            output_content = extraction_result.text

        # Save or print output
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(output_content, encoding="utf-8")
            logger.info("💾 Saved to: %s", output_file)
        else:
            # Print to stdout is acceptable for CLI tools
            sys.stdout.write(output_content)

    except (ValueError, RuntimeError, PermissionError, OSError):
        logger.exception("❌ Error processing %s", url)
        sys.exit(1)


def main() -> None:
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description="RegScraper - Ethical web scraping with robots.txt compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py -m regscraper https://example.com/doc.pdf
  py -m regscraper https://example.com/doc.pdf --output text.txt
  py -m regscraper https://example.com/doc.pdf --format json
  py -m regscraper https://example.com/doc.pdf --delay 5.0
        """,
    )

    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format (default: text)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--delay", "-d", type=float, default=2.0, help="Delay between requests in seconds (default: 2.0)")
    parser.add_argument("--user-agent", "-u", default="RegScraper/2.0", help="User agent string (default: RegScraper/2.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress all logging")

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the scraper
    asyncio.run(scrape_url(url=args.url, output_format=args.format, output_file=args.output, delay=args.delay, user_agent=args.user_agent))


if __name__ == "__main__":
    main()
