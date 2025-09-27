import os
from pathlib import Path
import json
from ..config import settings
from ..hashing import stable_hash


def ensure_dirs():
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.raw_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.json_dir).mkdir(parents=True, exist_ok=True)


def write_raw(url: str, content: str) -> str:
    fn = f"{Path(settings.raw_dir) / (stable_hash(url) + '.txt')}"
    Path(fn).write_text(content, encoding="utf-8")
    return fn


def write_json(obj: dict) -> str:
    sid = stable_hash(obj.get("source_url", "") + obj.get("full_text", ""))
    fn = f"{Path(settings.json_dir) / (sid + '.json')}"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return fn
