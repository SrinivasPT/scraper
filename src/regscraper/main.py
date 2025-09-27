import asyncio
from pathlib import Path
from .core.scraper import scrape_urls
from .config import settings

EXAMPLE_URLS = [
    "https://www.sec.gov/news/press-release/2024-05",
    "https://www.fda.gov/news-events/press-announcements",
    "https://ec.europa.eu/info/news/press-releases_en",
    "https://www.fda.gov/news-events/fda-briefing-documents/feed",
]


async def main():
    Path(settings.output_dir).mkdir(exist_ok=True, parents=True)
    results = await scrape_urls(EXAMPLE_URLS)
    ok = sum(1 for r in results if r)
    print(f"Processed {ok}/{len(results)} successfully")


if __name__ == "__main__":
    asyncio.run(main())
