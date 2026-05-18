from __future__ import annotations

import httpx
from ollama import ResponseError
from ollama._types import RequestError

from app.core.config import settings
from app.core.ollama_client import get_ollama_client
from app.models.schemas import ModelChatMessage

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's questions clearly and concisely."
)


class ModelChatError(RuntimeError):
    pass


def chat_with_model(messages: list[ModelChatMessage]) -> str:
    if not messages:
        raise ModelChatError("At least one message is required.")

    ollama_messages = []
    if messages[0].role != "system":
        ollama_messages.append({"role": "system", "content": SYSTEM_PROMPT})

    ollama_messages.extend(
        {"role": message.role, "content": message.content}
        for message in messages
    )

    try:
        response = get_ollama_client(settings.ollama_model_chat_timeout_seconds).chat(
            model=settings.ollama_chat_model,
            messages=ollama_messages,
            think=False,
            options=_chat_options(),
        )
    except httpx.TimeoutException as exc:
        msg = (
            f"Ollama at {settings.ollama_base_url} did not respond in time while generating "
            f"with model '{settings.ollama_chat_model}'. The server may be starting up, "
            "or the model may still be loading."
        )
        raise ModelChatError(msg) from exc
    except (RequestError, ResponseError) as exc:
        msg = _format_ollama_error(exc)
        raise ModelChatError(msg) from exc

    content = response.get("message", {}).get("content", "").strip()
    if not content:
        thinking = response.get("message", {}).get("thinking", "")
        if thinking:
            raise ModelChatError(
                "Ollama returned reasoning output but no final answer. "
                "Try a non-thinking model or keep think=False."
            )
        raise ModelChatError(
            "Ollama returned an empty answer. The model may be incompatible with the current chat settings."
        )
    return content


def _chat_options() -> dict[str, float | int]:
    return {
        "temperature": 0.7,
        "num_predict": settings.ollama_chat_num_predict,
    }


def _format_ollama_error(exc: Exception) -> str:
    error_text = str(exc).strip()
    model = settings.ollama_chat_model
    base_url = settings.ollama_base_url

    lowered = error_text.lower()
    if any(keyword in lowered for keyword in ("connection refused", "connect", "cannot connect", "failed to connect")):
        return (
            f"Could not connect to Ollama at {base_url}. Start Ollama, confirm it is running, "
            f"and make sure model '{model}' is pulled. Details: {error_text or type(exc).__name__}"
        )
    if any(keyword in lowered for keyword in ("not found", "model", "404", "no such model")):
        return (
            f"Ollama could not find model '{model}' at {base_url}. Pull it with "
            f"`ollama pull {model}` or change OLLAMA_CHAT_MODEL. Details: {error_text or type(exc).__name__}"
        )

    return (
        f"Could not generate a response with Ollama model '{model}' at {base_url}. "
        f"Details: {error_text or type(exc).__name__}"
    )
