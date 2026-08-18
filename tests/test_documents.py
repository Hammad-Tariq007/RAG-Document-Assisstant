"""Pure-logic tests: no database, no network, no model download."""

import pytest
from documents import extract_text
from fastapi import HTTPException


def test_extract_text_accepts_md():
    text = extract_text("notes.md", b"# Heading\n\nBody text")
    assert isinstance(text, str)
    assert "# Heading" in text
    assert "Body text" in text


def test_extract_text_accepts_csv():
    text = extract_text("data.csv", b"name,score\nada,10\n")
    assert "name,score" in text
    assert "ada,10" in text


def test_extract_text_accepts_uppercase_extension():
    assert "Body text" in extract_text("NOTES.MD", b"Body text")


def test_extract_text_txt_unchanged():
    assert extract_text("plain.txt", b"hello world") == "hello world"


def test_extract_text_rejects_unsupported_extension():
    with pytest.raises(HTTPException) as exc:
        extract_text("virus.exe", b"MZ\x90\x00")
    assert exc.value.status_code == 400
    assert isinstance(exc.value.detail, str) and exc.value.detail


def test_extract_text_rejects_file_with_no_extension():
    with pytest.raises(HTTPException) as exc:
        extract_text("README", b"some text")
    assert exc.value.status_code == 400


def test_extract_text_rejects_empty_md():
    with pytest.raises(HTTPException) as exc:
        extract_text("empty.md", b"   \n")
    assert exc.value.status_code == 400
