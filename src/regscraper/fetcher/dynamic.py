from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..throttler.domain import get_for, acquire_global
from ..throttler.robots import robots_cache


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=3, max=30))
async def fetch_dynamic_html(url: str) -> str:
    if not await robots_cache.is_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")

    dom_throttle = get_for(url)
    async with await acquire_global():
        await dom_throttle.acquire()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=settings.user_agent)
            await page.goto(url, wait_until="networkidle", timeout=45000)
            content = await page.content()
            await browser.close()
            return content
