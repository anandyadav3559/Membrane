from core.utils import generate_id

def split_text_into_chunks(text):
    """Splits text into word-level chunks with index and IDs."""
    final_chunks = text.split()
    chunks = []
    for idx, c in enumerate(final_chunks):
        chunks.append({
            "chunk_id": generate_id(f"chunk_{idx}"),
            "index": idx,
            "content": c
        })
    return chunks
