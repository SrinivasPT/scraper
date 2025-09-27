from __future__ import annotations

import io

import mammoth  # type: ignore[import-untyped]
from docx import Document as DocxDocument  # type: ignore[import-untyped]

from regscraper.interfaces import ContentType, DownloadResult, ExtractionResult, TextExtractor


class DocxTextExtractor(TextExtractor):
    """Extracts text from DOCX and DOC documents."""

    async def extract(self, download_result: DownloadResult) -> ExtractionResult:
        """Extract text from DOCX/DOC content."""
        metadata: dict[str, int | str] = {"format": "unknown", "paragraphs": 0}

        try:
            content_stream = io.BytesIO(download_result.content)

            # Detect if it's a legacy DOC file by URL or content sniffing
            is_doc_format = download_result.url.lower().endswith(".doc") or self._is_legacy_doc_format(download_result.content)

            if is_doc_format:
                # Use mammoth for .doc files
                result = mammoth.extract_raw_text(content_stream)  # type: ignore[misc]
                text = str(result.value or "").strip()  # type: ignore[misc]
                metadata["format"] = "doc"

                if result.messages:  # type: ignore[misc]
                    metadata["conversion_warnings"] = len(result.messages)  # type: ignore[misc]
            else:
                # Use python-docx for .docx files
                doc = DocxDocument(content_stream)  # type: ignore[misc]
                paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]  # type: ignore[misc]
                text = "\n".join(paragraphs)
                metadata["format"] = "docx"
                metadata["paragraphs"] = len(paragraphs)

        except (OSError, ValueError) as e:
            msg = f"DOCX text extraction failed: {e}"
            raise RuntimeError(msg) from e

        return ExtractionResult(text, metadata)

    def can_handle(self, content_type: ContentType) -> bool:
        """Check if this extractor can handle DOCX content."""
        return content_type == ContentType.DOCX

    def _is_legacy_doc_format(self, content: bytes) -> bool:
        """Heuristic to detect legacy DOC format."""
        # DOC files typically start with specific signatures
        doc_signatures = [
            b"\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1",  # OLE2 signature
            b"\\xdb\\xa5-\\x00\\x00\\x00",  # Alternative DOC signature
        ]

        return any(content.startswith(sig) for sig in doc_signatures)
