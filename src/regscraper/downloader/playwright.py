from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from regscraper.infrastructure import ThrottledRobotsChecker
from regscraper.interfaces import Downloader, DownloadResult


class PlaywrightDownloader(Downloader):
    """Playwright-based downloader for dynamic content."""

    def __init__(
        self,
        compliance_checker: ThrottledRobotsChecker,
        timeout: int = 45,
        user_agent: str = "RegScraper/2.0",
    ) -> None:
        self._compliance_checker = compliance_checker
        self._timeout = timeout * 1000  # Playwright uses milliseconds
        self._user_agent = user_agent

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=3, max=30))
    async def download(self, url: str) -> DownloadResult:
        """Download dynamic content using Playwright."""
        # Check robots.txt and acquire throttling lock
        await self._compliance_checker.check_and_acquire(url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self._user_agent)

                try:
                    await page.goto(url, wait_until="networkidle", timeout=self._timeout)
                    content_html = await page.content()

                    return DownloadResult(
                        content=content_html.encode("utf-8"),
                        content_type="text/html",
                        url=url,
                    )

                finally:
                    await browser.close()

        finally:
            # Always release throttling resources
            self._compliance_checker.release_throttle()
