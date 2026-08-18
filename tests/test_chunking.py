"""Pure-logic tests: no database, no network, no model download."""

from chunking import chunk_text


def test_chunk_text_returns_list_of_strings():
    chunks = chunk_text("hello world. " * 200)
    assert isinstance(chunks, list)
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_splits_long_input():
    assert len(chunk_text("word " * 2000)) > 1


def test_chunk_text_short_input_stays_single_chunk():
    assert len(chunk_text("short text")) == 1


def test_chunk_text_empty_input_does_not_crash():
    assert isinstance(chunk_text(""), list)
