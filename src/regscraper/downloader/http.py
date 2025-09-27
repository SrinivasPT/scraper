import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from regscraper.infrastructure import ThrottledRobotsChecker
from regscraper.interfaces import Downloader, DownloadResult


class HttpDownloader(Downloader):
    """HTTP downloader with robots.txt compliance and throttling."""

    def __init__(
        self,
        compliance_checker: ThrottledRobotsChecker,
        timeout: int = 30,
        user_agent: str = "RegScraper/2.0",
    ) -> None:
        self._compliance_checker = compliance_checker
        self._timeout = timeout
        self._user_agent = user_agent

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def download(self, url: str) -> DownloadResult:
        """Download content with compliance checks and retry logic."""
        # Check robots.txt and acquire throttling lock
        await self._compliance_checker.check_and_acquire(url)

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": self._user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Extract content type
                content_type = response.headers.get("content-type", "").split(";")[0]

                return DownloadResult(content=response.content, content_type=content_type, url=url)

        finally:
            # Always release throttling resources
            self._compliance_checker.release_throttle()
