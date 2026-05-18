from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.models.schemas import ModelChatRequest, ModelChatResponse
from app.services.model_chat import ModelChatError, chat_with_model

router = APIRouter(prefix="/model-chat", tags=["model-chat"])


@router.post("", response_model=ModelChatResponse)
def model_chat(request: ModelChatRequest) -> ModelChatResponse:
    try:
        answer = chat_with_model(request.messages)
    except ModelChatError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ModelChatResponse(answer=answer, model=settings.ollama_chat_model)
