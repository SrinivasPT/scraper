from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal


class RegulatoryDoc(BaseModel):
    title: str = Field(min_length=1)
    publication_date: Optional[str] = None  # ISO date string
    issuing_authority: Optional[str] = None
    document_type: Literal["press_release", "rule", "regulation", "notice", "other"]
    summary: Optional[str] = None
    full_text: str = Field(min_length=10)
    source_url: HttpUrl
