import json
import logging
import shutil
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import current_request_context
from app.models.schemas import DocumentChunk, DocumentText, PageText, UploadedDocument, UploadResponse
from app.services.chunking import chunk_pages
from app.services.document_loader import extract_text
from app.services.embeddings import EmbeddingError
from app.services.retrieval import IndexingError, delete_document_chunks, index_document_chunks

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
logger = logging.getLogger(__name__)


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_documents(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    file_names = [Path(file.filename or "").name for file in files]
    logger.info(
        "Upload request received files=%s request_context=%s",
        ", ".join(file_names),
        current_request_context(),
    )

    uploaded_documents: list[UploadedDocument] = []
    for file in files:
        uploaded_documents.append(_save_and_parse_file(file))

    return UploadResponse(documents=uploaded_documents)


def _save_and_parse_file(file: UploadFile) -> UploadedDocument:
    original_name = Path(file.filename or "").name
    file_type = Path(original_name).suffix.lower()
    if file_type not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload file=%s reason=unsupported_extension", original_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type for '{original_name}'. Allowed types: .pdf, .txt.",
        )

    document_id = str(uuid4())
    stored_file_name = f"{document_id}{file_type}"
    destination = settings.upload_dir / stored_file_name

    logger.info(
        "Saving upload file=%s document_id=%s destination=%s request_id=%s",
        original_name,
        document_id,
        destination,
        current_request_context()["request_id"],
    )

    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        pages = extract_text(destination, file_type)
        chunks = chunk_pages(document_id=document_id, source_file=original_name, pages=pages)
        if not chunks:
            raise ValueError(
                "No extractable text was found. Scanned/image-only PDFs need OCR before indexing."
            )
        index_document_chunks(chunks)
    except (EmbeddingError, IndexingError) as exc:
        logger.exception(
            "Upload indexing failed file=%s document_id=%s request_context=%s",
            original_name,
            document_id,
            current_request_context(),
        )
        _cleanup_failed_upload(destination, document_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Upload parsing failed file=%s document_id=%s request_context=%s",
            original_name,
            document_id,
            current_request_context(),
        )
        _cleanup_failed_upload(destination, document_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse '{original_name}'.",
        ) from exc

    uploaded_at = datetime.now(UTC)
    metadata = UploadedDocument(
        document_id=document_id,
        file_name=original_name,
        stored_file_name=stored_file_name,
        file_type=file_type.removeprefix("."),
        upload_timestamp=uploaded_at,
        page_count=len(pages) if file_type == ".pdf" else None,
        character_count=sum(len(page.text) for page in pages),
        chunk_count=len(chunks),
    )
    _write_metadata(metadata, pages, chunks)
    logger.info(
        "Upload complete file=%s document_id=%s pages=%s chunks=%s request_id=%s",
        original_name,
        document_id,
        len(pages),
        len(chunks),
        current_request_context()["request_id"],
    )
    return metadata


def _cleanup_failed_upload(destination: Path, document_id: str) -> None:
    destination.unlink(missing_ok=True)
    with suppress(Exception):
        delete_document_chunks(document_id)


def _write_metadata(
    metadata: UploadedDocument,
    pages: list[PageText],
    chunks: list[DocumentChunk],
) -> None:
    document_text = DocumentText(
        document_id=metadata.document_id,
        file_name=metadata.file_name,
        file_type=metadata.file_type,
        pages=pages,
    )
    metadata_path = settings.upload_dir / f"{metadata.document_id}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "metadata": metadata.model_dump(mode="json"),
                "document_text": document_text.model_dump(mode="json"),
                "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
