import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.model_chat import router as model_chat_router
from app.api.upload import router as upload_router
from app.core.config import settings
from app.core.logging import (
    bind_request_context,
    clear_request_context,
    configure_logging,
    current_request_context,
    new_request_id,
)


configure_logging()


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Local-first document Q&A API powered by Ollama and ChromaDB.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(chat_router)
    app.include_router(model_chat_router)
    app.include_router(documents_router)

    @app.on_event("startup")
    def log_startup() -> None:
        logger.info(
            "Starting %s in %s mode on http://%s:%s",
            settings.app_name,
            settings.environment,
            settings.backend_host,
            settings.backend_port,
        )
        logger.info("CORS origins: %s", ", ".join(settings.cors_origins) or "(none)")
        logger.info("Upload directory: %s", settings.upload_dir)
        logger.info("Chroma directory: %s", settings.chroma_persist_dir)
        logger.info("Chat memory directory: %s", settings.chat_memory_dir)
        logger.info(
            "Ollama config base_url=%s chat_model=%s embed_model=%s timeout_seconds=%s model_chat_timeout_seconds=%s",
            settings.ollama_base_url,
            settings.ollama_chat_model,
            settings.ollama_embed_model,
            settings.ollama_timeout_seconds,
            settings.ollama_model_chat_timeout_seconds,
        )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        client_host = request.client.host if request.client else "unknown"
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=client_host,
        )
        logger.info(
            "Request started query=%s content_length=%s content_type=%s",
            request.url.query or "-",
            request.headers.get("content-length", "-"),
            request.headers.get("content-type", "-"),
        )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception during request",
            )
            clear_request_context()
            raise

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request finished status=%s duration_ms=%.1f",
            response.status_code,
            elapsed_ms,
        )
        clear_request_context()
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Validation error errors=%s body=%s",
            exc.errors(),
            exc.body,
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "request_id": current_request_context()["request_id"],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled backend exception")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": current_request_context()["request_id"],
            },
        )

    return app


app = create_app()
