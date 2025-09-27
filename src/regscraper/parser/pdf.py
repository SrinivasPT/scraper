import io
import httpx
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


async def download_and_extract_pdf(url: str) -> str:
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.get(url)
        r.raise_for_status()
    data = io.BytesIO(r.content)

    text_parts: list[str] = []
    doc = fitz.open(stream=data, filetype="pdf")
    for page in doc:
        t = page.get_text("text")
        if t.strip():
            text_parts.append(t)
            continue
        # OCR fallback
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text_parts.append(pytesseract.image_to_string(img))
    return "\n".join(text_parts).strip()
