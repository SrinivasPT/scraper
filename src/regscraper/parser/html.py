from trafilatura import extract
from typing import Optional


def extract_clean_text(html: str) -> Optional[str]:
    return extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=False,
        output_format="txt",
    )
