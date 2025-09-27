from urllib.parse import urlparse


def classify_url(url: str) -> str:
    u = url.lower()
    if u.endswith(".pdf"):
        return "pdf"
    if u.endswith(".docx") or u.endswith(".doc"):
        return "docx"
    if u.endswith(".rss") or "/feed" in u or ".rss" in u:
        return "rss"
    return "html"


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()
