"""Nap danh sach tu khoa tu file JSON."""

import json
from pathlib import Path


def load_keywords(path: Path) -> list[str]:
    """Doc file JSON chua danh sach tu khoa.

    - Bo qua phan tu rong.
    - Chuan hoa ve chu thuong (match khong phan biet hoa thuong).
    - Loai bo trung lap, giu thu tu xuat hien dau tien.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"File tu khoa phai la JSON array: {path}")

    keywords: list[str] = []
    for item in raw:
        kw = str(item).strip().lower()
        if kw and kw not in keywords:
            keywords.append(kw)
    return keywords
