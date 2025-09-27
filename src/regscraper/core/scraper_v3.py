"""New scraper implementation using processor strategy pattern."""

import asyncio
from typing import Iterable, Optional, Union, Dict, List
from ..fetcher.session import HttpSession
from ..processors.factory import processor_factory
from ..extractor.llm import extract_with_llm
from ..storage.files import ensure_dirs, write_raw, write_json
from ..storage.db import open_db, upsert_document
from ..hashing import stable_hash
from ..logging import logger


async def finalize_document(url_for_raw: str, text: str, doc: dict) -> dict | None:
    """Finalize and store a processed document."""
    if not doc:
        return None
    raw_path = write_raw(url_for_raw, text)
    json_path = write_json(doc)
    async with await open_db() as db:
        await upsert_document(
            db,
            doc,
            raw_path,
            json_path,
            url_hash=stable_hash(doc["source_url"]),
            text_hash=stable_hash(doc["full_text"]),
        )
    return doc


async def process_single_v3(
    session: HttpSession, url: str
) -> Optional[Union[dict, Dict[str, List[dict]]]]:
    """Process a single URL using the new processor strategy pattern."""
    try:
        # Get appropriate processor for this URL
        processor = processor_factory.get_processor(url)
        processor_type = processor.get_processor_type()

        logger.info(f"Processing [{processor_type}] {url}")

        # Process the document
        result = await processor.process(session, url)

        if not result:
            logger.warning(f"No content extracted from {url}")
            return None

        # Handle RSS feeds differently (they return structured data already)
        if processor_type == "rss":
            # RSS processor returns {"items": [...]} with finalized documents
            if isinstance(result, dict) and "items" in result:
                finalized_items = []
                for item in result["items"]:
                    finalized = await finalize_document(
                        item["source_url"], item.get("full_text", ""), item
                    )
                    if finalized:
                        finalized_items.append(finalized)
                return {"items": finalized_items}
            return result

        # For other document types, extract with LLM and finalize
        if isinstance(result, str):
            doc = await extract_with_llm(result, url)
            return await finalize_document(url, result, doc)

        return result

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return None


async def scrape_urls_v3(
    urls: Iterable[str],
) -> list[Optional[Union[dict, Dict[str, List[dict]]]]]:
    """Scrape URLs using the new processor strategy pattern."""
    ensure_dirs()
    session = HttpSession()
    try:
        tasks = [process_single_v3(session, u) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
    finally:
        await session.close()


# Backward compatibility wrappers
async def process_single(session: HttpSession, url: str) -> dict | None:
    """Legacy wrapper for backward compatibility."""
    result = await process_single_v3(session, url)
    return result


async def scrape_urls(urls: Iterable[str]) -> list[dict | None]:
    """Legacy wrapper for backward compatibility."""
    return await scrape_urls_v3(urls)
