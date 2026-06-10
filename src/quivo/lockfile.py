""".quivo-lock.json helpers — what quivo installed, where, at which version."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

LOCK_FILE = ".quivo-lock.json"


def load_lock(target: Path) -> Optional[dict]:
    lock_path = target / LOCK_FILE
    if not lock_path.exists():
        return None
    with open(lock_path, encoding="utf-8") as f:
        return json.load(f)


def write_lock(target: Path, data: dict) -> Path:
    lock_path = target / LOCK_FILE
    lock_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return lock_path
