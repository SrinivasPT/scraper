import httpx
from urllib.robotparser import RobotFileParser
from collections import defaultdict
from . import domain as domain_throttle
from ..logging import logger
from ..config import settings
from ..utils.urls import domain_of


class RobotsCache:
    def __init__(self):
        self.cache: dict[str, RobotFileParser] = {}
        self.crawl_delay: dict[str, float] = defaultdict(lambda: settings.default_delay)

    async def load(self, url: str) -> RobotFileParser:
        dom = domain_of(url)
        if dom in self.cache:
            return self.cache[dom]

        robots_url = f"https://{dom}/robots.txt"
        rp = RobotFileParser()
        try:
            async with httpx.AsyncClient(
                http2=True, headers={"User-Agent": settings.user_agent}
            ) as client:
                r = await client.get(robots_url, timeout=10)
                if r.status_code == 200:
                    text = r.text
                    rp.parse(text.splitlines())
                    # naive crawl-delay parse
                    for line in text.splitlines():
                        if line.lower().startswith("crawl-delay"):
                            try:
                                delay = float(line.split(":", 1)[1].strip())
                                self.crawl_delay[dom] = max(delay, 0.5)
                            except Exception:
                                pass
                else:
                    rp.parse(["User-agent: *", "Allow: /"])
        except Exception as e:
            logger.warning(f"robots.txt fetch failed for {dom}: {e}")
            rp.parse(["User-agent: *", "Allow: /"])
        self.cache[dom] = rp
        return rp

    async def is_allowed(self, url: str) -> bool:
        rp = await self.load(url)
        return rp.can_fetch(settings.user_agent, url)


robots_cache = RobotsCache()
