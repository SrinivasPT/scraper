import aiosqlite
from pathlib import Path
from ..config import settings
from ..utils.time import utcnow_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  url_hash TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  title TEXT,
  publication_date TEXT,
  issuing_authority TEXT,
  document_type TEXT,
  summary TEXT,
  full_text TEXT,
  raw_path TEXT,
  json_path TEXT,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_text_hash ON documents(text_hash);
"""


async def open_db():
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(settings.db_path)
    await db.executescript(SCHEMA)
    return db


async def upsert_document(
    db, doc: dict, raw_path: str, json_path: str, url_hash: str, text_hash: str
):
    await db.execute(
        """
        INSERT OR IGNORE INTO documents (
          url, url_hash, text_hash, title, publication_date, issuing_authority,
          document_type, summary, full_text, raw_path, json_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc.get("source_url"),
            url_hash,
            text_hash,
            doc.get("title"),
            doc.get("publication_date"),
            doc.get("issuing_authority"),
            doc.get("document_type"),
            doc.get("summary"),
            doc.get("full_text"),
            raw_path,
            json_path,
            utcnow_iso(),
        ),
    )
    await db.commit()
