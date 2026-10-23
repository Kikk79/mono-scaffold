"""Strukturregeln, die import-linter nicht prüft.

- Kein Service und kein Router committet (Commit-Grenze ist die Anfrage, ADR-0003).
- Jedes Modul in docs/module-grenzen.md hat ein Paket mit den Pflichtdateien, und umgekehrt.
- Modul-`events.py` sind in app/main.py importiert (sonst fehlt der Handler zur Laufzeit).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES_DIR = ROOT / "app/modules"
PFLICHT = ("models.py", "schemas.py", "repository.py", "service.py", "router.py", "events.py")


def _modules_in_doku() -> set[str]:
    text = (ROOT / "docs/module-grenzen.md").read_text(encoding="utf-8")
    block = text.split("<!-- mono:modules-begin -->", 1)[1].split("<!-- mono:modules-end -->", 1)[0]
    return set(re.findall(r"^\| `([a-z][a-z0-9_]*)`", block, flags=re.MULTILINE))


def _modules_im_code() -> set[str]:
    return {p.name for p in MODULES_DIR.iterdir() if p.is_dir() and (p / "__init__.py").exists()}


def test_services_und_router_committen_nicht() -> None:
    treffer = [
        str(p.relative_to(ROOT))
        for p in list(MODULES_DIR.rglob("service.py")) + list(MODULES_DIR.rglob("router.py"))
        + list((ROOT / "app/read_models").rglob("*.py"))
        if re.search(r"\.commit\(", p.read_text(encoding="utf-8"))
    ]
    assert treffer == [], f"commit() außerhalb der Commit-Grenze: {treffer}"


def test_modultabelle_und_pakete_stimmen_ueberein() -> None:
    assert _modules_in_doku() == _modules_im_code()


def test_jedes_modul_hat_die_pflichtdateien() -> None:
    fehlend = [
        f"{m}/{f}"
        for m in _modules_im_code()
        for f in PFLICHT
        if not (MODULES_DIR / m / f).exists()
    ]
    assert fehlend == [], f"fehlende Dateien: {fehlend}"


def test_events_sind_in_main_importiert() -> None:
    main = (ROOT / "app/main.py").read_text(encoding="utf-8")
    fehlend = [m for m in _modules_im_code() if f"from app.modules.{m} import events" not in main]
    assert fehlend == [], f"events.py nicht in app/main.py importiert: {fehlend}"
