"""Test nap danh sach tu khoa."""

import json

import pytest

from app.keywords import load_keywords


def test_load_keywords_normalizes_deduplicates_and_filters(tmp_path):
    path = tmp_path / "keywords.json"
    path.write_text(
        json.dumps([" Free ", "free", "", "miễn phí AI", "Sales"], ensure_ascii=False),
        encoding="utf-8",
    )
    assert load_keywords(path) == ["free", "miễn phí ai", "sales"]


def test_load_keywords_converts_non_string_items(tmp_path):
    path = tmp_path / "keywords.json"
    path.write_text(json.dumps([123, "free"]), encoding="utf-8")
    assert load_keywords(path) == ["123", "free"]


def test_load_keywords_rejects_non_array(tmp_path):
    path = tmp_path / "keywords.json"
    path.write_text('{"keyword": "free"}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_keywords(path)
