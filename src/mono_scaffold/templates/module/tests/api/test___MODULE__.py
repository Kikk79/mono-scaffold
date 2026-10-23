"""API `__MODULE__`: anlegen, lesen, Duplikat, Statuswechsel, unbekannte ID."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

BASE = "/api/v1/__MODULE__"


def test_anlegen_und_lesen(client: TestClient) -> None:
    r = client.post(BASE, json={"name": "Erster"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Erster"
    assert body["status"] == "ACTIVE"

    r = client.get(f"{BASE}/{body['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == body["id"]


def test_doppelter_name_wird_mit_409_abgelehnt(client: TestClient) -> None:
    assert client.post(BASE, json={"name": "Doppelt"}).status_code == 201
    r = client.post(BASE, json={"name": "Doppelt"})
    assert r.status_code == 409
    assert r.json()["code"] == "conflict"


def test_leerer_name_ist_422(client: TestClient) -> None:
    assert client.post(BASE, json={"name": "   "}).status_code == 422


def test_deaktivieren_ist_nicht_zweimal_moeglich(client: TestClient) -> None:
    entity_id = client.post(BASE, json={"name": "Weg"}).json()["id"]
    r = client.post(f"{BASE}/{entity_id}/deactivate")
    assert r.status_code == 200
    assert r.json()["status"] == "INACTIVE"
    assert client.post(f"{BASE}/{entity_id}/deactivate").status_code == 409


def test_liste_filtert_nach_status(client: TestClient) -> None:
    a = client.post(BASE, json={"name": "Aktiv"}).json()["id"]
    b = client.post(BASE, json={"name": "Inaktiv"}).json()["id"]
    client.post(f"{BASE}/{b}/deactivate")
    ids = {i["id"] for i in client.get(BASE, params={"status": "INACTIVE"}).json()["items"]}
    assert ids == {b}
    assert a not in ids


def test_unbekannte_id_ist_404(client: TestClient) -> None:
    r = client.get(f"{BASE}/{uuid.uuid4()}")
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"
