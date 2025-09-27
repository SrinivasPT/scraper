"""Async tests for regscraper components."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from regscraper.infrastructure.robots import RobotsTxtChecker


class TestRobotsTxtChecker:
    """Test RobotsTxtChecker functionality."""

    def test_init(self):
        """Test RobotsTxtChecker initialization."""
        checker = RobotsTxtChecker()
        assert checker.user_agent == "RegScraper/2.0"

        custom_checker = RobotsTxtChecker("CustomBot/1.0")
        assert custom_checker.user_agent == "CustomBot/1.0"

    @pytest.mark.asyncio
    async def test_rss_feeds_always_allowed(self):
        """Test that RSS feeds are always allowed."""
        checker = RobotsTxtChecker()

        rss_urls = ["https://example.com/feed.rss", "https://example.com/feed.xml", "https://example.com/rss", "https://example.com/feed"]

        for url in rss_urls:
            result = await checker.is_allowed(url)
            assert result is True, f"RSS feed {url} should be allowed"

    @pytest.mark.asyncio
    async def test_robots_txt_compliance(self):
        """Test robots.txt compliance checking."""
        checker = RobotsTxtChecker()

        with patch("httpx.AsyncClient") as mock_client:
            # Mock robots.txt response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /private/\nAllow: /"

            mock_context = AsyncMock()
            mock_context.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_context

            # Should allow public URLs
            result = await checker.is_allowed("https://example.com/public/page")
            assert result is True

            # Should block private URLs
            result = await checker.is_allowed("https://example.com/private/secret")
            assert result is False

    @pytest.mark.asyncio
    async def test_robots_txt_not_found(self):
        """Test behavior when robots.txt is not found."""
        checker = RobotsTxtChecker()

        with patch("httpx.AsyncClient") as mock_client:
            # Mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404

            mock_context = AsyncMock()
            mock_context.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_context

            # Should allow access when robots.txt not found
            result = await checker.is_allowed("https://example.com/any-page")
            assert result is True

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        checker = RobotsTxtChecker()

        with patch("httpx.AsyncClient") as mock_client:
            # Mock network error during client context setup
            mock_client.side_effect = httpx.RequestError("Network error")

            # Should allow access on network errors (fallback behavior)
            result = await checker.is_allowed("https://example.com/page")
            assert result is True

    def test_crawl_delay_defaults(self):
        """Test crawl delay default behavior."""
        checker = RobotsTxtChecker()

        # Should return default delay for unknown domains
        delay = checker.get_crawl_delay("https://unknown.example.com")
        assert isinstance(delay, float)
        assert delay > 0
