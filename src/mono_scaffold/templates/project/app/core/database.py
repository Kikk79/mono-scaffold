"""Engine, Session und die Commit-Grenze einer Anfrage.

Regel (ADR-0003): Services und Router committen nie. Die Session einer Anfrage wird von
`TransactionMiddleware` committet, sobald der Handler eine Antwort < 400 erzeugt hat, und
sonst zurückgerollt. Ein Commit-Fehler wird so noch zur Fehlerantwort statt zur falschen 2xx.
Jobs (`app/jobs`) sind ihre eigene Commit-Grenze.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

_engine: Engine | None = None
SessionLocal = sessionmaker(class_=Session, expire_on_commit=False)


def get_engine() -> Engine:
    """Eine Engine je Prozess, erst beim ersten Zugriff erzeugt."""
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_db(request: Request) -> Session:
    """Session der Anfrage. Eine je Anfrage; Commit/Rollback macht die Middleware."""
    session = getattr(request.state, "db", None)
    if session is None:
        session = SessionLocal(bind=get_engine())
        request.state.db = session
    return session


class TransactionMiddleware(BaseHTTPMiddleware):
    """Commit vor dem Senden der Antwort; Rollback bei Fehlerstatus oder Ausnahme."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            await _finish(request, commit=False)
            raise
        await _finish(request, commit=response.status_code < 400)
        return response


async def _finish(request: Request, *, commit: bool) -> None:
    session: Session | None = getattr(request.state, "db", None)
    if session is None:
        return
    request.state.db = None
    try:
        if commit:
            await run_in_threadpool(session.commit)
        else:
            await run_in_threadpool(session.rollback)
    finally:
        await run_in_threadpool(session.close)
