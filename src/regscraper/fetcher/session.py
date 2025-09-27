import httpx
from ..config import settings


class HttpSession:
    def __init__(self):
        self.client = httpx.AsyncClient(
            http2=True,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )

    async def close(self):
        await self.client.aclose()
