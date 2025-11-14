from __future__ import annotations
from pathlib import Path
from typing import Iterable


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_lines(path: str | Path, lines: Iterable[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(str(line).rstrip("\n") + "\n")
