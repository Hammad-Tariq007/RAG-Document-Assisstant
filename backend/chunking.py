"""Text chunking — identical splitter and parameters as 01_chunk.py."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SEPARATORS, CHUNK_SIZE


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks using LangChain's recursive splitter.
    It tries paragraphs -> sentences -> words -> characters, in that order,
    so it avoids cutting in the middle of a word.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=CHUNK_SEPARATORS,
    )
    return splitter.split_text(text)
