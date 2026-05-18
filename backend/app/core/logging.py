from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar


request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
request_method_var: ContextVar[str] = ContextVar("request_method", default="-")
request_path_var: ContextVar[str] = ContextVar("request_path", default="-")
request_client_var: ContextVar[str] = ContextVar("request_client", default="-")

_LOGGING_CONFIGURED = False
_OLD_FACTORY = logging.getLogRecordFactory()


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s %(name)s "
            "[request_id=%(request_id)s method=%(request_method)s path=%(request_path)s "
            "client=%(request_client)s]: %(message)s"
        ),
    )
    logging.setLogRecordFactory(_record_factory)
    _LOGGING_CONFIGURED = True


def new_request_id() -> str:
    return uuid.uuid4().hex


def bind_request_context(
    *,
    request_id: str,
    method: str,
    path: str,
    client: str,
) -> None:
    request_id_var.set(request_id)
    request_method_var.set(method)
    request_path_var.set(path)
    request_client_var.set(client)


def clear_request_context() -> None:
    request_id_var.set("-")
    request_method_var.set("-")
    request_path_var.set("-")
    request_client_var.set("-")


def current_request_context() -> dict[str, str]:
    return {
        "request_id": request_id_var.get(),
        "request_method": request_method_var.get(),
        "request_path": request_path_var.get(),
        "request_client": request_client_var.get(),
    }


def _record_factory(*args, **kwargs):
    record = _OLD_FACTORY(*args, **kwargs)
    record.request_id = request_id_var.get()
    record.request_method = request_method_var.get()
    record.request_path = request_path_var.get()
    record.request_client = request_client_var.get()
    return record
