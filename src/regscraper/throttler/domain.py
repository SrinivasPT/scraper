import asyncio
import time
import random
from ..config import settings
from ..utils.urls import domain_of


class DomainThrottler:
    def __init__(self, domain: str, delay: float, concurrency: int):
        self.domain = domain
        self.delay = delay
        self.semaphore = asyncio.Semaphore(concurrency)
        self._last: float = 0.0

    async def acquire(self):
        async with self.semaphore:
            now = time.monotonic()
            elapsed = now - self._last
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed + random.uniform(0, 0.4))
            self._last = time.monotonic()


_global_sem = asyncio.Semaphore(settings.global_max_concurrency)
_domain_cache: dict[str, DomainThrottler] = {}

from ..config import settings


def get_for(url: str) -> DomainThrottler:
    dom = domain_of(url)
    if dom not in _domain_cache:
        override = settings.site_overrides.get(dom, {})
        delay = float(override.get("delay", settings.default_delay))
        concurrency = int(override.get("concurrency", settings.default_concurrency))
        _domain_cache[dom] = DomainThrottler(dom, delay, concurrency)
    return _domain_cache[dom]


async def acquire_global():
    return _global_sem
