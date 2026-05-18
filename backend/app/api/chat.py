import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, ChatSession, ChatSessionsResponse
from app.services.chat_memory import ChatSessionNotFoundError, get_chat_session, list_chat_sessions
from app.services.embeddings import EmbeddingError
from app.services.rag_pipeline import RagGenerationError, answer_question, stream_answer_events
from app.services.retrieval import RetrievalError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return answer_question(
            question=request.question,
            document_ids=request.document_ids,
            session_id=request.session_id,
            top_k=request.top_k,
        )
    except (EmbeddingError, RetrievalError, RagGenerationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", response_model=ChatSessionsResponse)
def sessions() -> ChatSessionsResponse:
    return ChatSessionsResponse(sessions=list_chat_sessions())


@router.get("/sessions/{session_id}", response_model=ChatSession)
def session_detail(session_id: str) -> ChatSession:
    try:
        return get_chat_session(session_id)
    except ChatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


def _sse_events(request: ChatRequest):
    try:
        for event in stream_answer_events(
            question=request.question,
            document_ids=request.document_ids,
            session_id=request.session_id,
            top_k=request.top_k,
        ):
            yield _format_sse(event)
    except (EmbeddingError, RetrievalError, RagGenerationError) as exc:
        yield _format_sse({"type": "error", "detail": str(exc)})
    except Exception as exc:
        yield _format_sse({"type": "error", "detail": "Unexpected streaming error."})
        raise exc


def _format_sse(payload: dict) -> str:
    event_type = payload.get("type", "message")
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
