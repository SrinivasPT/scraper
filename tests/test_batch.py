"""Test the batch scraping functionality."""

import logging
import time
from urllib.parse import urlparse

import pytest

from regscraper.batch import BatchScraper, scrape_urls_batch

logger = logging.getLogger(__name__)


class TestBatchScraper:
    """Test batch scraping with shared throttling."""

    @pytest.fixture
    def mixed_urls(self) -> list[str]:
        """URLs from different domains for testing shared throttling."""
        return [
            "https://www.sec.gov/newsroom/press-releases/2025-126-sec-seeks-public-comment-improve-rules-residential-mortgage-backed-securities-asset-backed",
            "https://www.sec.gov/newsroom/press-releases/2025-125-sec-announces-departure-chief-operating-officer-ken-johnson",
            "https://www.sec.gov/newsroom/press-releases/2025-124-sec-announces-agenda-panelists-sec-cftc-roundtable-regulatory-harmonization-efforts",
            "https://www.sec.gov/newsroom/press-releases/2025-121-sec-approves-generic-listing-standards-commodity-based-trust-shares",
            "https://www.sec.gov/newsroom/press-releases/2025-115-james-moloney-named-director-division-corporation-finance",
            "https://www.sec.gov/newsroom/press-releases/2025-103-sec-creates-task-force-tap-artificial-intelligence-enhanced-innovation-efficiency-across-agency",
        ]

    @pytest.mark.asyncio
    async def test_batch_scraper_shared_throttling(self, mixed_urls: list[str]) -> None:
        """Test that BatchScraper properly applies shared throttling."""
        logger.info("🔄 Testing BatchScraper with shared throttling")

        # Create scraper with SEC-specific throttling
        scraper = BatchScraper(
            site_overrides={"www.sec.gov": {"delay": 5.0, "concurrency": 1, "type": "static"}},
            default_delay=1.0,
            user_agent="Test Scraper/1.0",
        )

        # Time the batch processing
        start_time = time.time()
        results = await scraper.scrape_urls(urls=mixed_urls, max_concurrent=5)
        total_time = time.time() - start_time

        # Analyze results
        successful = [r for r in results if r["success"]]
        sec_results = [r for r in results if "sec.gov" in r["url"]]

        logger.info("📊 BatchScraper completed in %.2fs", total_time)
        logger.info("📊 Success rate: %d/%d URLs", len(successful), len(results))
        logger.info("📊 SEC URLs processed: %d", len(sec_results))

        # Assertions
        assert len(results) == len(mixed_urls), f"Expected {len(mixed_urls)} results"
        assert len(successful) >= 2, f"Expected at least 2 successes, got {len(successful)}"

        # Should respect SEC throttling (2 SEC URLs + 1s delay = at least 2s for SEC domain)
        # Plus time for other domains
        assert total_time >= 20.0, f"Too fast ({total_time:.2f}s), shared throttling not working"
        assert total_time <= 35.0, f"Too slow ({total_time:.2f}s), may have issues"

        # Validate result structure
        for result in results:
            assert "url" in result
            assert "success" in result
            assert "text" in result
            assert "metadata" in result

        # Validate successful results have content
        for result in successful:
            assert len(result["text"]) > 100, f"Too little content from {result['url']}"

    @pytest.mark.asyncio
    async def test_convenience_function(self, mixed_urls: list[str]) -> None:
        """Test the convenience scrape_urls_batch function."""
        logger.info("🔄 Testing convenience function")

        start_time = time.time()
        results = await scrape_urls_batch(
            urls=mixed_urls[:2],  # Just first 2 URLs for speed
            max_concurrent=3,
        )
        total_time = time.time() - start_time

        successful = [r for r in results if r["success"]]

        logger.info("📊 Convenience function completed in %.2fs", total_time)
        logger.info("📊 Success rate: %d/%d URLs", len(successful), len(results))

        # Assertions
        assert len(results) == 2, "Expected 2 results"
        assert len(successful) >= 1, "Expected at least 1 success"
        assert total_time >= 1.0, "Should take some time due to throttling"
        assert total_time <= 10.0, "Should not be too slow"

    def test_domain_counting_logic(self) -> None:
        """Test URL domain parsing logic that would be used in batch processing."""
        urls = ["https://www.sec.gov/doc1", "https://www.sec.gov/doc2", "https://www.bis.org/doc1", "not-a-url"]

        # Test the same domain parsing logic that the batch scraper uses
        domain_counts: dict[str, int] = {}
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain:  # Only count if we got a valid domain
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                else:  # No netloc means invalid URL
                    domain_counts["invalid"] = domain_counts.get("invalid", 0) + 1
            except (ValueError, AttributeError):
                domain_counts["invalid"] = domain_counts.get("invalid", 0) + 1

        assert domain_counts["www.sec.gov"] == 2
        assert domain_counts["www.bis.org"] == 1
        assert domain_counts["invalid"] == 1

    def test_scraper_initialization(self) -> None:
        """Test that BatchScraper initializes properly with default and custom configurations."""
        # Test that a scraper with no overrides initializes successfully
        default_scraper = BatchScraper()
        assert default_scraper is not None

        # Test that we can create a scraper with explicit site overrides
        custom_scraper = BatchScraper(site_overrides={"test.com": {"delay": 1.0, "concurrency": 2, "type": "static"}})
        assert custom_scraper is not None

        # Test that scraper accepts configuration parameters
        configured_scraper = BatchScraper(default_delay=5.0, default_concurrency=3, user_agent="Test Agent")
        assert configured_scraper is not None
