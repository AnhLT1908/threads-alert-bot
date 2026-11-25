"""So khop tu khoa voi noi dung bai viet."""

import re
import unicodedata

_WORD_KEYWORD_PATTERNS: dict[str, re.Pattern[str]] = {}


def _strip_accents(value: str) -> str:
    """Bo dau (VD "miễn phí" -> "mien phi").

    Bai viet tieng Viet tren Threads thuong khong dau; chuan hoa de
    tu khoa co dau van khop voi bai viet khong dau.
    """
    normalized = unicodedata.normalize("NFD", value)
    return "".join(
        char for char in normalized if not unicodedata.combining(char)
    )


def text_matches(text: str, keyword: str) -> bool:
    """Kiem tra tu khoa co xuat hien trong text (khong phan biet hoa thuong, dau).

    - Tu khoa chi gom chu/so va khoang trang (VD "free", "sales",
      "miễn phí AI"): match NGUYEN CUM voi word boundary de tranh
      nhieu kieu "freedom" trung tu khoa "free".
    - Tu khoa co ky tu dac biet (VD "AI/ML"): match chuoi con.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return False

    text_lower = _strip_accents(text.lower())
    keyword = _strip_accents(keyword)

    if keyword.isascii() and keyword.replace(" ", "").isalnum():
        pattern = _WORD_KEYWORD_PATTERNS.get(keyword)
        if pattern is None:
            pattern = re.compile(
                rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
            )
            _WORD_KEYWORD_PATTERNS[keyword] = pattern
        return pattern.search(text_lower) is not None

    return keyword in text_lower
