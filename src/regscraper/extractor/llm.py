import json
from openai import AsyncOpenAI
from ..config import settings
from ..logging import logger
from .schema import RegulatoryDoc

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


PROMPT = (
    "You are a regulatory document analyst. Extract the following fields strictly as JSON:\n"
    "- title: string\n"
    "- publication_date: ISO 8601 date (YYYY-MM-DD) or null\n"
    "- issuing_authority: string or null\n"
    "- document_type: one of ['press_release','rule','regulation','notice','other']\n"
    "- summary: 1-2 sentence summary or null\n"
    "- full_text: the clean main body\n"
    "- source_url: original URL\n"
    "Return only a JSON object with these keys."
)


async def extract_with_llm(content: str, url: str) -> dict | None:
    if not content or len(content.strip()) < 10:
        return None
    try:
        resp = await client().chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "Return only a single JSON object."},
                {
                    "role": "user",
                    "content": f"{PROMPT}\n\nText from {url}:\n{content[:16000]}",
                },
            ],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        data["source_url"] = url
        doc = RegulatoryDoc(**data)
        return doc.model_dump()
    except Exception as e:
        logger.error(f"LLM extraction failed for {url}: {e}")
        return None
