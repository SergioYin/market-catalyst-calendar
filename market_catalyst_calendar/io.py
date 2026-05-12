"""Input and deterministic output helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .models import Dataset, parse_dataset


def read_text(path: Optional[str]) -> str:
    if path in {None, "-"}:
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def read_json(path: Optional[str]) -> Dict[str, Any]:
    return json.loads(read_text(path))


def load_dataset(path: Optional[str]) -> Dataset:
    return parse_dataset(read_json(path))


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
