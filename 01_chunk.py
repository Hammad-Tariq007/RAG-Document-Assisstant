from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_document(path: str) -> str:
    """Read a text file and return its full contents as one string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks using LangChain's recursive splitter.
    It tries paragraphs -> sentences -> words -> characters, in that order,
    so it avoids cutting in the middle of a word.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],   # priority order of split points
    )
    return splitter.split_text(text)


if __name__ == "__main__":
    text = load_document("sample.txt")
    print(f"Loaded document: {len(text)} characters\n")

    chunks = chunk_text(text)
    print(f"Split into {len(chunks)} chunks:\n")

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i} ({len(chunk)} chars) ---")
        print(chunk)
        print()