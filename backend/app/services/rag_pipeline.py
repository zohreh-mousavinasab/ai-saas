from uuid import uuid4

import httpx
from ollama import ResponseError
from ollama._types import RequestError

from app.core.config import settings
from app.core.ollama_client import get_ollama_client
from app.models.schemas import ChatResponse, ChatSource, MatchingChunk
from app.services.chat_memory import append_exchange, format_recent_history, get_recent_messages
from app.services.retrieval import retrieve_relevant_chunks

SYSTEM_PROMPT = (
    "You are DocMind AI, a local document question-answering assistant. "
    "Answer only from the provided document context. "
    "If the context does not contain the answer, say that you do not know based on the uploaded documents. "
    "Keep the answer concise and cite the provided source labels like [S1] when they support the answer."
)


class RagGenerationError(RuntimeError):
    pass


def answer_question(
    *,
    question: str,
    document_ids: list[str] | None = None,
    session_id: str | None = None,
    top_k: int = 5,
) -> ChatResponse:
    active_session_id = session_id or str(uuid4())
    history = get_recent_messages(active_session_id)
    matching_chunks = retrieve_relevant_chunks(
        question=question,
        document_ids=document_ids,
        top_k=top_k,
    )
    answer = _generate_answer(question, matching_chunks, format_recent_history(history))
    append_exchange(session_id=active_session_id, question=question, answer=answer)
    return ChatResponse(
        answer=answer,
        sources=_build_sources(matching_chunks),
        matching_chunks=matching_chunks,
        session_id=active_session_id,
    )


def stream_answer_events(
    *,
    question: str,
    document_ids: list[str] | None = None,
    session_id: str | None = None,
    top_k: int = 5,
):
    active_session_id = session_id or str(uuid4())
    history = get_recent_messages(active_session_id)
    matching_chunks = retrieve_relevant_chunks(
        question=question,
        document_ids=document_ids,
        top_k=top_k,
    )
    yield {
        "type": "metadata",
        "session_id": active_session_id,
        "sources": [source.model_dump(mode="json") for source in _build_sources(matching_chunks)],
        "matching_chunks": [chunk.model_dump(mode="json") for chunk in matching_chunks],
    }

    answer_parts: list[str] = []
    for token in _stream_answer_tokens(question, matching_chunks, format_recent_history(history)):
        answer_parts.append(token)
        yield {"type": "token", "token": token}

    answer = "".join(answer_parts).strip()
    if not answer:
        msg = "Ollama returned an empty answer."
        raise RagGenerationError(msg)

    append_exchange(session_id=active_session_id, question=question, answer=answer)
    yield {
        "type": "done",
        "answer": answer,
        "session_id": active_session_id,
        "sources": [source.model_dump(mode="json") for source in _build_sources(matching_chunks)],
        "matching_chunks": [chunk.model_dump(mode="json") for chunk in matching_chunks],
    }


def _generate_answer(question: str, chunks: list[MatchingChunk], history: str) -> str:
    try:
        response = get_ollama_client(settings.ollama_model_chat_timeout_seconds).chat(
            model=settings.ollama_chat_model,
            messages=_build_messages(question, chunks, history),
            think=False,
            options=_chat_options(),
        )
    except httpx.TimeoutException as exc:
        msg = (
            f"Ollama chat model '{settings.ollama_chat_model}' timed out after "
            f"{settings.ollama_model_chat_timeout_seconds:g} seconds. The model may still be loading; "
            "try again or use a smaller chat model."
        )
        raise RagGenerationError(msg) from exc
    except (RequestError, ResponseError) as exc:
        msg = f"Could not generate an answer with Ollama model '{settings.ollama_chat_model}'."
        raise RagGenerationError(msg) from exc

    message = response.get("message", {})
    content = message.get("content", "").strip()
    if not content:
        thinking = message.get("thinking", "")
        if thinking:
            msg = (
                "Ollama returned reasoning output but no final answer. "
                "Try a non-thinking model or keep think=False."
            )
        else:
            msg = "Ollama returned an empty answer."
        raise RagGenerationError(msg)
    return content


def _stream_answer_tokens(question: str, chunks: list[MatchingChunk], history: str):
    try:
        stream = get_ollama_client(settings.ollama_model_chat_timeout_seconds).chat(
            model=settings.ollama_chat_model,
            messages=_build_messages(question, chunks, history),
            stream=True,
            think=False,
            options=_chat_options(),
        )
        for event in stream:
            token = event.get("message", {}).get("content", "")
            if token:
                yield token
    except httpx.TimeoutException as exc:
        msg = (
            f"Ollama chat model '{settings.ollama_chat_model}' timed out after "
            f"{settings.ollama_model_chat_timeout_seconds:g} seconds. The model may still be loading; "
            "try again or use a smaller chat model."
        )
        raise RagGenerationError(msg) from exc
    except (RequestError, ResponseError) as exc:
        msg = f"Could not stream an answer with Ollama model '{settings.ollama_chat_model}'."
        raise RagGenerationError(msg) from exc


def _build_messages(question: str, chunks: list[MatchingChunk], history: str) -> list[dict[str, str]]:
    context = _build_context(chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Recent chat history:\n{history}\n\n"
                f"Document context:\n{context}\n\n"
                f"Question:\n{question}\n\n"
                "Answer using only the document context."
            ),
        },
    ]


def _build_context(chunks: list[MatchingChunk]) -> str:
    if not chunks:
        return "No relevant document chunks were retrieved."

    context_blocks: list[str] = []
    for source_number, chunk in enumerate(chunks, start=1):
        page = f", page {chunk.page_number}" if chunk.page_number is not None else ""
        score = (
            f", similarity {chunk.similarity_score:.4f}"
            if chunk.similarity_score is not None
            else ""
        )
        context_blocks.append(
            f"[S{source_number}: {chunk.source_file}{page}, chunk {chunk.chunk_index}{score}]\n"
            f"{chunk.text}"
        )
    return "\n\n".join(context_blocks)


def _chat_options() -> dict[str, float | int]:
    return {
        "temperature": 0.1,
        "num_predict": settings.ollama_chat_num_predict,
    }


def _build_sources(chunks: list[MatchingChunk]) -> list[ChatSource]:
    sources: list[ChatSource] = []
    seen: set[tuple[str, int]] = set()
    for chunk in chunks:
        key = (chunk.document_id, chunk.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            ChatSource(
                document_id=chunk.document_id,
                file_name=chunk.source_file,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                excerpt=_excerpt(chunk.text),
                similarity_score=chunk.similarity_score,
            )
        )
    return sources


def _excerpt(text: str, max_length: int = 240) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_length:
        return clean
    return f"{clean[: max_length - 3].rstrip()}..."
