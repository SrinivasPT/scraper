"""Infrastructure components for robots.txt and throttling."""

import httpx
import asyncio
from urllib.robotparser import RobotFileParser
from collections import defaultdict
from typing import Dict
from urllib.parse import urlparse


class RobotsTxtChecker:
    """Robots.txt compliance checker with caching."""

    def __init__(self, user_agent: str = "RegScraper/2.0"):
        self.user_agent = user_agent
        self._cache: Dict[str, RobotFileParser] = {}
        self._crawl_delays: Dict[str, float] = defaultdict(lambda: 2.0)

    async def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        domain = self._get_domain(url)
        parser = await self._get_robots_parser(domain)
        return parser.can_fetch(self.user_agent, url)

    def get_crawl_delay(self, url: str) -> float:
        """Get crawl delay for domain."""
        domain = self._get_domain(url)
        return self._crawl_delays[domain]

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()

    async def _get_robots_parser(self, domain: str) -> RobotFileParser:
        """Get robots.txt parser for domain (cached)."""
        if domain in self._cache:
            return self._cache[domain]

        robots_url = f"https://{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    robots_url, headers={"User-Agent": self.user_agent}
                )

                if response.status_code == 200:
                    lines = response.text.splitlines()
                    parser.parse(lines)
                    self._parse_crawl_delay(domain, response.text)
                else:
                    # Default: allow all
                    parser.set_url(robots_url)
                    parser.parse(["User-agent: *", "Allow: /"])

        except Exception:
            # Default: allow all on error
            parser.set_url(robots_url)
            parser.parse(["User-agent: *", "Allow: /"])

        self._cache[domain] = parser
        return parser

    def _parse_crawl_delay(self, domain: str, robots_content: str) -> None:
        """Parse crawl-delay directive from robots.txt."""
        for line in robots_content.splitlines():
            if line.lower().strip().startswith("crawl-delay"):
                try:
                    delay = float(line.split(":", 1)[1].strip())
                    self._crawl_delays[domain] = max(delay, 0.5)  # Minimum 0.5s
                    break
                except (ValueError, IndexError):
                    continue


class DomainThrottler:
    """Per-domain rate limiting with semaphores."""

    def __init__(self, default_delay: float = 2.0, default_concurrency: int = 2):
        self.default_delay = default_delay
        self.default_concurrency = default_concurrency
        self._domain_locks: Dict[str, asyncio.Semaphore] = {}
        self._last_request: Dict[str, float] = {}
        self._global_semaphore = asyncio.Semaphore(10)  # Global limit

    async def acquire(self, url: str) -> None:
        """Acquire throttling lock for URL's domain."""
        domain = self._get_domain(url)

        # Global throttling first
        await self._global_semaphore.acquire()

        try:
            # Domain-specific throttling
            domain_lock = self._get_domain_lock(domain)
            await domain_lock.acquire()

            try:
                # Rate limiting
                await self._enforce_delay(domain)
            finally:
                domain_lock.release()

        except Exception:
            self._global_semaphore.release()
            raise

    def release_global(self) -> None:
        """Release global semaphore."""
        self._global_semaphore.release()

    def configure_domain(self, domain: str, delay: float, concurrency: int) -> None:
        """Configure specific domain settings."""
        self._domain_locks[domain] = asyncio.Semaphore(concurrency)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()

    def _get_domain_lock(self, domain: str) -> asyncio.Semaphore:
        """Get or create semaphore for domain."""
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Semaphore(self.default_concurrency)
        return self._domain_locks[domain]

    async def _enforce_delay(self, domain: str) -> None:
        """Enforce delay between requests to same domain."""
        import time

        now = time.time()

        if domain in self._last_request:
            elapsed = now - self._last_request[domain]
            if elapsed < self.default_delay:
                await asyncio.sleep(self.default_delay - elapsed)

        self._last_request[domain] = time.time()


class ThrottledRobotsChecker:
    """Combined robots.txt checker with throttling."""

    def __init__(self, robots_checker: RobotsTxtChecker, throttler: DomainThrottler):
        self._robots_checker = robots_checker
        self._throttler = throttler

    async def check_and_acquire(self, url: str) -> None:
        """Check robots.txt compliance and acquire throttling lock."""
        # Fast robots.txt check first (fail fast)
        if not await self._robots_checker.is_allowed(url):
            raise PermissionError(f"URL blocked by robots.txt: {url}")

        # Then acquire throttling lock
        await self._throttler.acquire(url)

    def release_throttle(self) -> None:
        """Release throttling resources."""
        self._throttler.release_global()
