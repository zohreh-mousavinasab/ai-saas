from app.models.schemas import DocumentChunk, PageText

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 250


def chunk_pages(
    *,
    document_id: str,
    source_file: str,
    pages: list[PageText],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        msg = "chunk_size must be greater than 0"
        raise ValueError(msg)
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        msg = "chunk_overlap must be at least 0 and less than chunk_size"
        raise ValueError(msg)

    chunks: list[DocumentChunk] = []
    for page in pages:
        for text in _split_text(page.text, chunk_size, chunk_overlap):
            chunk_index = len(chunks)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}:{chunk_index}",
                    document_id=document_id,
                    source_file=source_file,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    text=text,
                )
            )
    return chunks


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()

        if end < len(normalized):
            last_space = chunk.rfind(" ")
            minimum_chunk_length = chunk_size // 2
            if last_space >= minimum_chunk_length:
                end = start + last_space
                chunk = normalized[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(normalized):
            break
        start = max(end - chunk_overlap, 0)

    return chunks
