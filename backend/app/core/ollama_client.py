from functools import lru_cache

import ollama

from app.core.config import settings


@lru_cache
def get_ollama_client(timeout_seconds: float | None = None) -> ollama.Client:
    return ollama.Client(
        host=settings.ollama_base_url,
        timeout=timeout_seconds if timeout_seconds is not None else settings.ollama_timeout_seconds,
    )
