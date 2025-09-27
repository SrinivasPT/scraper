from .domain import DomainThrottler
from .robots import RobotsTxtChecker


class ThrottledRobotsChecker:
    """Combined robots.txt checker with throttling."""

    def __init__(self, robots_checker: RobotsTxtChecker, throttler: DomainThrottler) -> None:
        self._robots_checker = robots_checker
        self._throttler = throttler

    async def check_and_acquire(self, url: str) -> None:
        """Check robots.txt compliance and acquire throttling lock."""
        # Fast robots.txt check first (fail fast)
        if not await self._robots_checker.is_allowed(url):
            msg = f"URL blocked by robots.txt: {url}"
            raise PermissionError(msg)

        # Then acquire throttling lock
        await self._throttler.acquire(url)

    def release_throttle(self) -> None:
        """Release throttling resources."""
        self._throttler.release_global()
