"""So khop tu khoa voi noi dung bai viet."""

import re

_WORD_KEYWORD_PATTERNS: dict[str, re.Pattern[str]] = {}


def text_matches(text: str, keyword: str) -> bool:
    """Kiem tra tu khoa co xuat hien trong text (khong phan biet hoa thuong).

    - Tu khoa chi gom chu/so va khoang trang (VD "free", "sales",
      "free trial"): match NGUYEN CUM voi word boundary de tranh
      nhieu kieu "freedom" trung tu khoa "free".
    - Tu khoa co dau / ky tu dac biet (VD "miễn phí AI"): match
      chuoi con thong thuong.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    text_lower = text.lower()

    if keyword.isascii() and keyword.replace(" ", "").isalnum():
        pattern = _WORD_KEYWORD_PATTERNS.get(keyword)
        if pattern is None:
            pattern = re.compile(
                rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
            )
            _WORD_KEYWORD_PATTERNS[keyword] = pattern
        return pattern.search(text_lower) is not None

    return keyword in text_lower
