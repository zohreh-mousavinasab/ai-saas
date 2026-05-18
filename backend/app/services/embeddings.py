from collections.abc import Sequence

import httpx
from ollama import ResponseError
from ollama._types import RequestError

from app.core.config import settings
from app.core.ollama_client import get_ollama_client


class EmbeddingError(RuntimeError):
    pass


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    batch_size = max(settings.ollama_embed_batch_size, 1)
    for start in range(0, len(texts), batch_size):
        embeddings.extend(_embed_batch(texts[start : start + batch_size]))

    return embeddings


def _embed_batch(texts: Sequence[str]) -> list[list[float]]:
    try:
        response = get_ollama_client().embed(
            model=settings.ollama_embed_model,
            input=list(texts),
            truncate=True,
        )
    except httpx.TimeoutException as exc:
        msg = (
            f"Ollama embedding model '{settings.ollama_embed_model}' timed out after "
            f"{settings.ollama_timeout_seconds:g} seconds. Try again after the model finishes "
            "loading, or lower OLLAMA_EMBED_BATCH_SIZE for large PDFs."
        )
        raise EmbeddingError(msg) from exc
    except (RequestError, ResponseError) as exc:
        msg = f"Could not generate embeddings with Ollama model '{settings.ollama_embed_model}'."
        raise EmbeddingError(msg) from exc

    embeddings = response.get("embeddings", [])
    if len(embeddings) != len(texts):
        msg = "Ollama returned an unexpected number of embeddings."
        raise EmbeddingError(msg)

    return [list(embedding) for embedding in embeddings]
