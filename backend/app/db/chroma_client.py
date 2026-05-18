from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings

COLLECTION_NAME = "document_chunks"


@lru_cache
def get_chroma_client() -> chromadb.api.ClientAPI:
    return chromadb.PersistentClient(path=str(settings.chroma_persist_dir))


@lru_cache
def get_document_collection() -> Collection:
    return get_chroma_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Document chunks indexed for local RAG retrieval."},
    )
