"""Testbasis: echte Postgres-Test-DB, Schema je Sitzung neu, ein Savepoint je Test.

- Nur gegen PostgreSQL (`TEST_DATABASE_URL`, DB-Name endet auf `_test`), nie SQLite.
- `public` wird zu Beginn jeder Sitzung neu angelegt und per `create_all` aus den Modellen
  aufgebaut (Migrationen prüfen eigene Tests, Up/Down/Up).
- Jeder Test läuft in einer äußeren Transaktion, die am Ende zurückrollt; `session.commit()`
  im Test gibt nur den Savepoint frei. Der `TestClient` nutzt dieselbe Session (Override von
  `get_db`), die Transaktions-Middleware greift dabei nicht.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

os.environ.setdefault("ENVIRONMENT", "test")

from app.core import model_registry  # alle Modelle laden
from app.core.config import get_settings
from app.core.database import get_db
from app.main import app


def _test_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or get_settings().TEST_DATABASE_URL
    if not url or not url.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
        pytest.exit(
            "TEST_DATABASE_URL fehlt oder der DB-Name endet nicht auf `_test` "
            "(Schutz: die Sitzung legt das Schema `public` neu an).",
            returncode=3,
        )
    return url


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = create_engine(_test_url())
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    model_registry.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as conn:
        outer = conn.begin()
        sess = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield sess
        finally:
            sess.close()
            outer.rollback()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
