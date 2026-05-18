import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import settings
from app.models.schemas import ChatMessage, ChatSession, ChatSessionSummary

MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_CHARACTERS = 4000


class ChatSessionNotFoundError(RuntimeError):
    pass


def get_recent_messages(session_id: str | None, limit: int = MAX_HISTORY_MESSAGES) -> list[ChatMessage]:
    if not session_id:
        return []
    try:
        session = get_chat_session(session_id)
    except ChatSessionNotFoundError:
        return []
    return session.messages[-limit:]


def append_exchange(*, session_id: str, question: str, answer: str) -> ChatSession:
    existing = _read_session(session_id)
    now = datetime.now(UTC)

    if existing is None:
        messages: list[ChatMessage] = []
        created_at = now
        title = _make_title(question)
    else:
        messages = existing.messages
        created_at = existing.created_at
        title = existing.title

    messages.extend(
        [
            ChatMessage(role="user", content=question, created_at=now),
            ChatMessage(role="assistant", content=answer, created_at=now),
        ]
    )
    session = ChatSession(
        session_id=session_id,
        created_at=created_at,
        updated_at=now,
        message_count=len(messages),
        title=title,
        messages=messages,
    )
    _write_session(session)
    return session


def list_chat_sessions() -> list[ChatSessionSummary]:
    sessions = [_to_summary(session) for session in _iter_sessions()]
    return sorted(sessions, key=lambda session: session.updated_at, reverse=True)


def get_chat_session(session_id: str) -> ChatSession:
    session = _read_session(session_id)
    if session is None:
        msg = f"Chat session '{session_id}' was not found."
        raise ChatSessionNotFoundError(msg)
    return session


def format_recent_history(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No previous messages."
    lines = []
    for message in messages:
        speaker = "User" if message.role == "user" else "Assistant"
        lines.append(f"{speaker}: {message.content}")
    history = "\n".join(lines)
    if len(history) <= MAX_HISTORY_CHARACTERS:
        return history
    return history[-MAX_HISTORY_CHARACTERS:]


def _iter_sessions() -> list[ChatSession]:
    sessions: list[ChatSession] = []
    for path in settings.chat_memory_dir.glob("*.json"):
        session = _read_session(path.stem)
        if session is not None:
            sessions.append(session)
    return sessions


def _read_session(session_id: str) -> ChatSession | None:
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ChatSession.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _write_session(session: ChatSession) -> None:
    _session_path(session.session_id).write_text(
        json.dumps(session.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _session_path(session_id: str) -> Path:
    safe_session_id = "".join(character for character in session_id if character.isalnum() or character in "-_")
    return settings.chat_memory_dir / f"{safe_session_id}.json"


def _to_summary(session: ChatSession) -> ChatSessionSummary:
    return ChatSessionSummary(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=session.message_count,
        title=session.title,
    )


def _make_title(question: str, max_length: int = 80) -> str:
    clean = " ".join(question.split())
    if len(clean) <= max_length:
        return clean
    return f"{clean[: max_length - 3].rstrip()}..."
