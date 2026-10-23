"""Liveness ohne DB, Readiness mit DB-Ping, Request-ID im Antwort-Header."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_antwortet_ohne_datenbank(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_pingt_die_datenbank(client: TestClient) -> None:
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "database": "ok"}


def test_request_id_wird_uebernommen_oder_vergeben(client: TestClient) -> None:
    r = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"
    assert len(client.get("/health").headers["X-Request-ID"]) == 32
