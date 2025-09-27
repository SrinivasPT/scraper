import asyncio
from urllib.parse import urlparse


class DomainThrottler:
    """Per-domain rate limiting with semaphores."""

    def __init__(self, default_delay: float = 2.0, default_concurrency: int = 2) -> None:
        self.default_delay = default_delay
        self.default_concurrency = default_concurrency
        self._domain_locks: dict[str, asyncio.Semaphore] = {}
        self._last_request: dict[str, float] = {}
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
