#!/usr/bin/env python3
"""Batch processing module for scraping multiple URLs with shared throttling."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory

logger = logging.getLogger(__name__)


class BatchScraper:
    """Batch scraper with shared throttling across domains."""

    def __init__(
        self,
        site_overrides: dict[str, dict[str, Any]] | None = None,
        default_delay: float = 2.0,
        default_concurrency: int = 2,
        user_agent: str = "RegScraper/2.0 (Batch)",
    ) -> None:
        """Initialize batch scraper with shared infrastructure."""
        # Set up common domain configurations
        if site_overrides is None:
            site_overrides = self._get_default_site_configs()

        self._site_overrides = site_overrides

        # Create shared factories
        self._downloader_factory = DownloaderFactory(
            site_overrides=site_overrides, default_delay=default_delay, default_concurrency=default_concurrency, user_agent=user_agent
        )
        self._extractor_factory = ExtractorFactory()

    def _get_default_site_configs(self) -> dict[str, dict[str, Any]]:
        """Get default configurations for common domains.

        Includes conservative defaults for unknown domains via the '*' wildcard key.
        """
        return {
            # Conservative defaults for any domain not explicitly configured
            "*": {"delay": 3.0, "concurrency": 1, "type": "static"},
            # Known domain-specific configurations
            "sec.gov": {"delay": 2.0, "concurrency": 1, "type": "static"},
            "bis.org": {"delay": 1.5, "concurrency": 2, "type": "static"},
            "federalregister.gov": {"delay": 1.0, "concurrency": 2, "type": "static"},
            "treasury.gov": {"delay": 2.0, "concurrency": 1, "type": "static"},
            "cftc.gov": {"delay": 1.5, "concurrency": 2, "type": "static"},
            "occ.gov": {"delay": 2.0, "concurrency": 1, "type": "static"},
        }

    def _get_domain_config(self, domain: str) -> dict[str, Any]:
        """Get configuration for a domain, falling back to conservative defaults if not found."""
        domain_config = self._site_overrides.get(domain)
        if domain_config is not None:
            return domain_config

        # Fall back to conservative defaults for unknown domains
        conservative_defaults = self._site_overrides.get("*", {})
        if conservative_defaults:
            return conservative_defaults

        # Final fallback if no wildcard is defined
        return {"delay": 3.0, "concurrency": 1, "type": "static"}

    async def scrape_urls(
        self,
        urls: list[str],
        output_format: str = "json",
        output_dir: Path | None = None,
        max_concurrent: int = 10,
        save_individually: bool = False,
    ) -> list[dict[str, Any]]:
        """Scrape multiple URLs with proper rate limiting."""
        logger.info("🚀 Starting batch scraping of %d URLs", len(urls))

        # Group URLs by domain for better logging
        domain_counts = self._count_urls_by_domain(urls)
        for domain, count in domain_counts.items():
            domain_config = self._get_domain_config(domain)
            delay = domain_config.get("delay", 2.0)
            concurrency = domain_config.get("concurrency", 2)
            logger.info("📊 Domain %s: %d URLs (delay=%.1fs, concurrency=%d)", domain, count, delay, concurrency)

        # Create semaphore for global concurrency control
        global_semaphore = asyncio.Semaphore(max_concurrent)

        # Process all URLs concurrently with shared throttling
        start_time = time.time()

        tasks = [self._scrape_single_url(url, global_semaphore, idx) for idx, url in enumerate(urls)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Process results
        processed_results: list[dict[str, Any]] = []
        success_count = 0
        error_count = 0

        for idx, result in enumerate(results):
            processed_result: dict[str, Any]
            if isinstance(result, Exception):
                logger.error("❌ URL %d failed with exception: %s", idx, result)
                processed_result = {"url": urls[idx], "success": False, "error": str(result), "text": "", "metadata": {}}
                error_count += 1
            else:
                # result is guaranteed to be dict[str, Any] here
                processed_result = result  # type: ignore[assignment]
                if processed_result.get("success", False):
                    success_count += 1
                else:
                    error_count += 1

            processed_results.append(processed_result)

        # Log summary
        logger.info("📊 Batch completed in %.2fs: %d success, %d errors", total_time, success_count, error_count)
        logger.info("📊 Average time per URL: %.2fs", total_time / len(urls))

        # Save results if requested
        if output_dir:
            await self._save_results(processed_results, output_dir, output_format, save_individually)

        return processed_results

    async def _scrape_single_url(self, url: str, global_semaphore: asyncio.Semaphore, idx: int) -> dict[str, Any]:
        """Scrape a single URL with shared throttling."""
        async with global_semaphore:
            try:
                logger.debug("⬇️  [%d] Processing: %s", idx, url)

                # Use shared factory (with shared throttler)
                downloader = self._downloader_factory.create_downloader(url)
                extractor = self._extractor_factory.create_extractor(url)

                # Download with domain-specific throttling
                download_result = await downloader.download(url)
                logger.debug("✅ [%d] Downloaded %d bytes", idx, len(download_result.content))

                # Extract content
                extraction_result = await extractor.extract(download_result)
                logger.debug("✅ [%d] Extracted %d chars", idx, len(extraction_result.text))

                # Safely handle metadata
                metadata_dict = {}
                try:
                    metadata = getattr(extraction_result, "metadata", {})
                    if metadata:
                        metadata_json = json.dumps(metadata, default=str)
                        metadata_dict = json.loads(metadata_json)
                except (ValueError, TypeError, AttributeError):
                    metadata_dict = {"error": "metadata not serializable"}

                return {
                    "url": url,
                    "success": True,
                    "error": "",
                    "text": extraction_result.text,
                    "metadata": metadata_dict,
                    "content_type": download_result.content_type,
                    "content_length": len(download_result.content),
                    "text_length": len(extraction_result.text),
                }

            except (ValueError, RuntimeError, OSError, ConnectionError, TimeoutError) as e:
                logger.warning("❌ [%d] Failed %s: %s", idx, url, e)
                return {
                    "url": url,
                    "success": False,
                    "error": str(e),
                    "text": "",
                    "metadata": {},
                    "content_type": "",
                    "content_length": 0,
                    "text_length": 0,
                }

    def _count_urls_by_domain(self, urls: list[str]) -> dict[str, int]:
        """Count URLs by domain for logging."""
        domain_counts: dict[str, int] = {}
        for url in urls:
            try:
                domain = urlparse(url).netloc.lower()
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            except (ValueError, AttributeError):
                domain_counts["invalid"] = domain_counts.get("invalid", 0) + 1
        return domain_counts

    async def _save_results(self, results: list[dict[str, Any]], output_dir: Path, output_format: str, save_individually: bool) -> None:
        """Save results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        if save_individually:
            # Save each result as separate file
            for idx, result in enumerate(results):
                filename = f"result_{idx:04d}_{self._sanitize_filename(result['url'])}"
                if output_format == "json":
                    filepath = output_dir / f"{filename}.json"
                    filepath.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
                else:
                    filepath = output_dir / f"{filename}.txt"
                    filepath.write_text(result["text"], encoding="utf-8")

            logger.info("💾 Saved %d individual files to %s", len(results), output_dir)
        else:
            # Save all results in one file
            if output_format == "json":
                filepath = output_dir / "batch_results.json"
                filepath.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                filepath = output_dir / "batch_results.txt"
                text_content = "\n\n" + "=" * 80 + "\n\n".join(f"URL: {r['url']}\n\n{r['text']}" for r in results if r["success"])
                filepath.write_text(text_content, encoding="utf-8")

            logger.info("💾 Saved batch results to %s", filepath)

    def _sanitize_filename(self, url: str) -> str:
        """Sanitize URL for filename."""
        try:
            domain = urlparse(url).netloc.lower()
            return domain.replace(".", "_")
        except (ValueError, AttributeError):
            return "unknown"


# Convenience function for simple batch processing
async def scrape_urls_batch(
    urls: list[str], site_overrides: dict[str, dict[str, Any]] | None = None, output_dir: Path | None = None, max_concurrent: int = 10
) -> list[dict[str, Any]]:
    """Simple batch scraping function."""
    scraper = BatchScraper(site_overrides=site_overrides)
    return await scraper.scrape_urls(urls=urls, output_dir=output_dir, max_concurrent=max_concurrent)
