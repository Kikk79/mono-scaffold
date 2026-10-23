"""Betriebs-Logging (docs/conventions/logging.md).

- Logger je Modul: `logging.getLogger(__name__)`.
- Eine Zeile je Anfrage: Methode, Pfad ohne Query-String, Status, Dauer; `request_id` und
  Antwort-Header `X-Request-ID`.
- Fachereignisse im Service über `log_after_commit` – erst nach dem Commit geschrieben, bei
  Rollback verworfen (sonst meldet das Log Buchungen, die es nie gab). Ablehnungen direkt
  über `log_event`.
- Nie geloggt: Authorization-Header, Passwörter, Tokens, Query-Strings, Request-Bodies,
  Namen, Adressen.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from sqlalchemy import event
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_FORMAT = "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler.addFilter(_RequestIdFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())


def _fields(fields: dict[str, Any]) -> str:
    return " ".join(f"{k}={v}" for k, v in fields.items())


def log_event(logger: logging.Logger, event_name: str, **fields: Any) -> None:
    """Sofort schreiben (Ablehnungen, Zustandsmeldungen)."""
    logger.info("%s %s", event_name, _fields(fields))


def log_after_commit(
    session: Session, logger: logging.Logger, event_name: str, **fields: Any
) -> None:
    """Fachereignis vormerken; geschrieben wird erst im `after_commit` der Session."""
    pending = session.info.setdefault("pending_log", [])
    pending.append((logger, event_name, fields, request_id_var.get()))


@event.listens_for(Session, "after_commit")
def _flush_pending_log(session: Session) -> None:
    for logger, event_name, fields, rid in session.info.pop("pending_log", []):
        token = request_id_var.set(rid)
        try:
            logger.info("%s %s", event_name, _fields(fields))
        finally:
            request_id_var.reset(token)


@event.listens_for(Session, "after_rollback")
def _drop_pending_log(session: Session) -> None:
    session.info.pop("pending_log", None)


def log_app_error(logger: logging.Logger, status_code: int, code: str, message: str) -> None:
    """`AppError` < 500 ist INFO (erwartete Ablehnung), ab 500 ERROR."""
    if status_code >= 500:
        logger.error("app_error status=%s code=%s message=%s", status_code, code, message)
    else:
        logger.info("app_error status=%s code=%s", status_code, code)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Vergibt die `request_id` und schreibt eine Zeile je Anfrage."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = rid
        token = request_id_var.set(rid)
        started = time.perf_counter()
        logger = logging.getLogger("app.request")
        try:
            try:
                response = await call_next(request)
            except Exception:
                logger.exception(
                    "%s %s status=500 duration_ms=%.1f",
                    request.method,
                    request.url.path,
                    (time.perf_counter() - started) * 1000,
                )
                raise
            logger.info(
                "%s %s status=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
            )
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_var.reset(token)
