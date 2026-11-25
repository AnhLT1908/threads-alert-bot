"""Test matcher so khop tu khoa."""

from app.matcher import text_matches


def test_accented_keyword_matches_accented_text():
    assert text_matches("Khóa học Miễn phí AI cho người mới", "miễn phí AI")


def test_accented_keyword_matches_unaccented_text():
    # bai viet tieng Viet khong dau van khop tu khoa co dau
    assert text_matches("Khoa hoc mien phi AI cho nguoi moi", "miễn phí AI")


def test_unaccented_keyword_matches_accented_text():
    assert text_matches("Khóa học Miễn phí AI", "mien phi AI")


def test_case_insensitive_match():
    assert text_matches("PROMOTE your product now", "promote")
    assert text_matches("Big SALES today", "sales")


def test_whole_word_prevents_false_positive():
    # "freedom" khong duoc tinh la trung tu khoa "free"
    assert not text_matches("Freedom of speech matters", "free")
    # "sales" khong trung "salesperson"
    assert not text_matches("Hire a salesperson", "sales")


def test_whole_word_matches_standalone_with_punctuation():
    assert text_matches("Get it for free!", "free")
    assert text_matches("Sale, 50% off", "sale")


def test_multi_word_english_keyword_matches_whole_phrase():
    assert text_matches("Join our free trial today", "free trial")
    assert not text_matches("Free coffee for the trial run", "free trial")


def test_special_character_keyword_uses_substring():
    assert text_matches("Tim hieu AI/ML cho nguoi moi", "AI/ML")


def test_empty_keyword_returns_false():
    assert not text_matches("anything", "")
    assert not text_matches("anything", "   ")


def test_empty_text_returns_false():
    assert not text_matches("", "free")
