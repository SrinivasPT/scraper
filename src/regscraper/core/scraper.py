from typing import Iterable

# Import new v3 processor-based functions
from .scraper_v3 import scrape_urls_v3, process_single_v3
from ..fetcher.session import HttpSession

# Legacy imports kept for backward compatibility with legacy functions
from ..fetcher.static import fetch_html
from ..fetcher.dynamic import fetch_dynamic_html
from ..parser.html import extract_clean_text
from ..parser.pdf_v2 import download_and_extract_pdf_v2
from ..parser.docx_v2 import download_and_extract_docx_v2
from ..parser.rss import fetch_and_parse_rss
from ..extractor.llm import extract_with_llm
from ..storage.files import write_raw, write_json
from ..storage.db import open_db, upsert_document
from ..hashing import stable_hash
from ..logging import logger


async def finalize_document(url_for_raw: str, text: str, doc: dict) -> dict | None:
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


async def process_rss_url(url: str) -> dict | None:
    items = await fetch_and_parse_rss(url)
    results: list[dict] = []
    for itm in items:
        content = f"{itm.get('title','')}\n\n{itm.get('summary','')}"
        doc = await extract_with_llm(content, itm.get("link", url))
        if doc:
            finalized = await finalize_document(doc["source_url"], content, doc)
            if finalized:
                results.append(finalized)
    return {"items": results}


async def process_document_url(
    session: HttpSession, url: str, kind: str
) -> dict | None:
    if kind == "html":
        html = await fetch_html(session, url)
        text = extract_clean_text(html) or ""
    elif kind == "pdf":
        text = await download_and_extract_pdf_v2(url)
    elif kind == "docx":
        text = await download_and_extract_docx_v2(url)
    else:
        # Heuristic: dynamic if site override says so
        html = await fetch_dynamic_html(url)
        text = extract_clean_text(html) or ""

    if not text.strip():
        logger.warning(f"No text extracted: {url}")
        return None

    doc = await extract_with_llm(text, url)
    return await finalize_document(url, text, doc)


async def process_single(session: HttpSession, url: str) -> dict | None:
    """Process single URL - now uses processor strategy pattern."""
    return await process_single_v3(session, url)


async def scrape_urls(urls: Iterable[str]) -> list[dict | None]:
    """Scrape URLs - now uses processor strategy pattern."""
    return await scrape_urls_v3(urls)
