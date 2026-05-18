from app.db.chroma_client import get_document_collection
from app.models.schemas import DocumentChunk, MatchingChunk
from app.services.embeddings import embed_texts


class IndexingError(RuntimeError):
    pass


class RetrievalError(RuntimeError):
    pass


def index_document_chunks(chunks: list[DocumentChunk]) -> int:
    if not chunks:
        return 0

    embeddings = embed_texts([chunk.text for chunk in chunks])
    try:
        collection = get_document_collection()
        collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[_chunk_metadata(chunk) for chunk in chunks],
        )
    except Exception as exc:
        msg = "Could not index document chunks in ChromaDB."
        raise IndexingError(msg) from exc
    return len(chunks)


def delete_document_chunks(document_id: str) -> None:
    get_document_collection().delete(where={"document_id": document_id})


def retrieve_relevant_chunks(
    *,
    question: str,
    document_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[MatchingChunk]:
    query_embedding = embed_texts([question])[0]
    where = _document_filter(document_ids)

    try:
        results = get_document_collection().query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        msg = "Could not retrieve relevant chunks from ChromaDB."
        raise RetrievalError(msg) from exc

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: list[MatchingChunk] = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances, strict=False):
        page_number = metadata.get("page_number")
        chunks.append(
            MatchingChunk(
                chunk_id=chunk_id,
                document_id=str(metadata.get("document_id", "")),
                source_file=str(metadata.get("source_file", "")),
                page_number=page_number if page_number else None,
                chunk_index=int(metadata.get("chunk_index", 0)),
                text=text,
                distance=float(distance) if distance is not None else None,
                similarity_score=_distance_to_similarity(distance),
            )
        )
    return chunks


def _chunk_metadata(chunk: DocumentChunk) -> dict[str, str | int]:
    return {
        "document_id": chunk.document_id,
        "source_file": chunk.source_file,
        "page_number": chunk.page_number if chunk.page_number is not None else 0,
        "chunk_index": chunk.chunk_index,
    }


def _document_filter(document_ids: list[str] | None) -> dict | None:
    if not document_ids:
        return None
    if len(document_ids) == 1:
        return {"document_id": document_ids[0]}
    return {"document_id": {"$in": document_ids}}


def _distance_to_similarity(distance: float | None) -> float | None:
    if distance is None:
        return None
    if distance < 0:
        return None
    return round(1 / (1 + float(distance)), 4)
