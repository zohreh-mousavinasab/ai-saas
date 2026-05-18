from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PageText(BaseModel):
    page_number: int | None = None
    text: str


class UploadedDocument(BaseModel):
    document_id: str
    file_name: str
    stored_file_name: str
    file_type: str
    upload_timestamp: datetime
    page_count: int | None = None
    character_count: int
    chunk_count: int


class UploadResponse(BaseModel):
    documents: list[UploadedDocument]


class DocumentsResponse(BaseModel):
    documents: list[UploadedDocument]


class DocumentText(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    pages: list[PageText]


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_file: str
    page_number: int | None = None
    chunk_index: int
    text: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    document_ids: list[str] | None = None
    session_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class ChatSource(BaseModel):
    document_id: str
    file_name: str
    page_number: int | None = None
    chunk_index: int
    excerpt: str
    similarity_score: float | None = None


class MatchingChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_file: str
    page_number: int | None = None
    chunk_index: int
    text: str
    distance: float | None = None
    similarity_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    matching_chunks: list[MatchingChunk]
    session_id: str


class ModelChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ModelChatRequest(BaseModel):
    messages: list[ModelChatMessage]


class ModelChatResponse(BaseModel):
    answer: str
    model: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatSessionSummary(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    title: str | None = None


class ChatSession(ChatSessionSummary):
    messages: list[ChatMessage]


class ChatSessionsResponse(BaseModel):
    sessions: list[ChatSessionSummary]
