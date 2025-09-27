from tenacity import retry, stop_after_attempt, wait_exponential
from .session import HttpSession
from ..throttler.domain import get_for, acquire_global
from ..throttler.robots import robots_cache


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def fetch_html(session: HttpSession, url: str) -> str:
    if not await robots_cache.is_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")

    dom_throttle = get_for(url)
    async with await acquire_global():
        await dom_throttle.acquire()
        r = await session.client.get(url, timeout=20)
        r.raise_for_status()
        return r.text
