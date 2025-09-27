from collections import defaultdict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsTxtChecker:
    """Robots.txt compliance checker with caching."""

    def __init__(self, user_agent: str = "RegScraper/2.0") -> None:
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}
        self._crawl_delays: dict[str, float] = defaultdict(lambda: 2.0)

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
                response = await client.get(robots_url, headers={"User-Agent": self.user_agent})

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
