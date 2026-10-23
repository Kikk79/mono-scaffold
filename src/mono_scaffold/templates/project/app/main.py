"""FastAPI-Einstieg (Composition Root): Router, Event-Handler, Middleware, Fehlerantworten.

Einzige Stelle, die Fachmodule zusammensteckt. `mono module …` trägt neue Module zwischen den
Markern ein; nichts von Hand ändern.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import TransactionMiddleware
from app.core.exceptions import AppError
from app.core.health import router as health_router
from app.core.logging import RequestLoggingMiddleware, configure_logging, log_app_error

# mono:imports-begin
# mono:imports-end

configure_logging(get_settings().LOG_LEVEL)
_docs = get_settings().docs_enabled
_log = logging.getLogger(__name__)

app = FastAPI(
    title="__TITLE__",
    version="0.1.0",
    docs_url="/docs" if _docs else None,
    redoc_url="/redoc" if _docs else None,
    openapi_url="/openapi.json" if _docs else None,
)
# Reihenfolge: zuletzt hinzugefügt = außen. Logging außen, Transaktion innen.
app.add_middleware(TransactionMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(AppError)
async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
    log_app_error(_log, exc.status_code, exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code, content={"code": exc.code, "message": exc.message}
    )


@app.exception_handler(RequestValidationError)
async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Eingabe ungültig, bitte die markierten Felder prüfen.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    rid = getattr(request.state, "request_id", "")
    _log.exception("unbehandelte Ausnahme request_id=%s", rid)
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": f"Interner Fehler (Request-ID {rid})."},
    )


app.include_router(health_router)
# mono:include-begin
# mono:include-end
