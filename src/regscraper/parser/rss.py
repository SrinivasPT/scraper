import httpx
import feedparser


async def fetch_and_parse_rss(url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
    feed = feedparser.parse(r.text)
    items = []
    for e in feed.entries:
        items.append(
            {
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "published": e.get("published", ""),
                "summary": e.get("summary", ""),
                "source_url": url,
            }
        )
    return items
