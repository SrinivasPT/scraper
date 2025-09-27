from typing import Any
from urllib.parse import urlparse

from regscraper.infrastructure import (
    DomainThrottler,
    RobotsTxtChecker,
    ThrottledRobotsChecker,
)
from regscraper.interfaces import Downloader

from .HttpDownloader import HttpDownloader
from .PlaywrightDownloader import PlaywrightDownloader

SiteConfig = dict[str, dict[str, Any]]


class DownloaderFactory:
    """Factory for creating downloader with site-specific configurations."""

    def __init__(
        self,
        site_overrides: SiteConfig,
        default_delay: float = 2.0,
        default_concurrency: int = 2,
        user_agent: str = "RegScraper/2.0",
    ) -> None:
        self._site_overrides = site_overrides
        self._user_agent = user_agent

        # Create shared infrastructure
        self._robots_checker = RobotsTxtChecker(user_agent)
        self._throttler = DomainThrottler(default_delay, default_concurrency)

        # Configure domain-specific throttling
        self._configure_domain_throttling()

        # Create compliance checker
        self._compliance_checker = ThrottledRobotsChecker(self._robots_checker, self._throttler)

    def create_downloader(self, url: str) -> Downloader:
        """Create appropriate downloader based on URL and site configuration."""
        domain = self._get_domain(url)
        site_config = self._site_overrides.get(domain, {})

        # Determine if site needs dynamic downloading
        site_type = site_config.get("type", "static")

        if site_type == "dynamic":
            return PlaywrightDownloader(compliance_checker=self._compliance_checker, user_agent=self._user_agent)
        return HttpDownloader(compliance_checker=self._compliance_checker, user_agent=self._user_agent)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()

    def _configure_domain_throttling(self) -> None:
        """Configure throttling for specific domains."""
        for domain, config in self._site_overrides.items():
            delay = config.get("delay", 2.0)
            concurrency = config.get("concurrency", 2)

            self._throttler.configure_domain(domain, delay, concurrency)


# Example site configuration (from original codebase)
DEFAULT_SITE_OVERRIDES: SiteConfig = {
    "sec.gov": {"delay": 5.0, "concurrency": 1, "type": "static"},
    "ec.europa.eu": {"delay": 3.0, "concurrency": 2, "type": "static"},
    "fda.gov": {"delay": 2.5, "concurrency": 2, "type": "static"},
}
