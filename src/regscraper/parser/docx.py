import io
import httpx
from docx import Document
import mammoth


async def download_and_extract_docx(url: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()

    if url.lower().endswith(".doc"):
        # Convert .doc to text via mammoth
        result = mammoth.extract_raw_text(io.BytesIO(r.content))
        return (result.value or "").strip()

    doc = Document(io.BytesIO(r.content))
    paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras)
