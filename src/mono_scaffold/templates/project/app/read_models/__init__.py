"""Modulübergreifende, schreibgeschützte Lesesichten (ADR-0002, Regel 3).

Darf ORM-Modelle und Schemas der gelesenen Module importieren, ruft aber nie fremde Services
oder Repositories und schreibt nie (Contracts `read-models-nur-lesen`, `*-repository-privat`).
Eine Datei je Sicht, z. B. `document_flow.py`, plus `router.py` unter `/api/v1/views/…`.
"""
