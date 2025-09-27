"""DOCX and DOC text extraction."""

import io
from typing import BinaryIO
from docx import Document
import mammoth
from .base import TextExtractor
from ..logging import logger


class DocxExtractor(TextExtractor):
    """Extracts text from DOCX and DOC files."""

    async def extract_text(
        self, content: bytes | BinaryIO, is_doc_format: bool = False
    ) -> str:
        """Extract text from DOCX or DOC content."""
        logger.debug(f"Extracting text from {'DOC' if is_doc_format else 'DOCX'}")

        # Handle both bytes and BinaryIO
        if isinstance(content, bytes):
            stream = io.BytesIO(content)
        else:
            stream = content

        try:
            if is_doc_format:
                # Use mammoth for .doc files
                result = mammoth.extract_raw_text(stream)
                extracted_text = (result.value or "").strip()

                if result.messages:
                    logger.debug(f"Mammoth conversion messages: {result.messages}")

            else:
                # Use python-docx for .docx files
                doc = Document(stream)
                paragraphs = [
                    p.text for p in doc.paragraphs if p.text and p.text.strip()
                ]
                extracted_text = "\n".join(paragraphs)

            logger.debug(f"Extracted {len(extracted_text)} characters from document")
            return extracted_text

        except Exception as e:
            logger.error(f"Error extracting text from document: {e}")
            raise

    def supports_format(self, file_extension: str) -> bool:
        """Check if this extractor supports DOCX/DOC files."""
        return file_extension.lower() in [".docx", ".doc"]


# Default instance
default_docx_extractor = DocxExtractor()
