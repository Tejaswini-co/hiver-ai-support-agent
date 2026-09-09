"""Small, schema-tolerant readers for the source dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".jsonl", ".json"}


def discover_files(input_path: str | Path) -> list[Path]:
    path = Path(input_path)
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")
    files = sorted(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not files:
        raise FileNotFoundError(f"No CSV/JSON/JSONL files found under {path}")
    return files


def read_source(path: str | Path, *, nrows: int | None = None) -> pd.DataFrame:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source, nrows=nrows, low_memory=False)
    if suffix in {".json", ".jsonl"}:
        return pd.read_json(source, lines=suffix == ".jsonl")
    raise ValueError(f"Unsupported source format: {source.suffix}")


def read_many(paths: Iterable[Path], *, nrows: int | None = None) -> pd.DataFrame:
    frames = [read_source(path, nrows=nrows) for path in paths]
    return pd.concat(frames, ignore_index=True, sort=False)