import json

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import DocumentsResponse, UploadedDocument

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentsResponse)
def documents() -> DocumentsResponse:
    return DocumentsResponse(documents=_list_uploaded_documents())


def _list_uploaded_documents() -> list[UploadedDocument]:
    documents: list[UploadedDocument] = []
    for path in settings.upload_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            metadata = payload.get("metadata", payload)
            documents.append(UploadedDocument.model_validate(metadata))
        except (OSError, json.JSONDecodeError, ValueError):
            continue

    return sorted(
        documents,
        key=lambda document: document.upload_timestamp,
        reverse=True,
    )
