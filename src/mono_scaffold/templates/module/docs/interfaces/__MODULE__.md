# Interface `__MODULE__`

- Stand: __DATE__ (angelegt von `mono module`)
- Darf importieren: __IMPORTS__ (siehe [module-grenzen.md](../module-grenzen.md))
- Bindend für das Modul. Abweichungen hier dokumentieren, nicht still umsetzen.

## 1. Zweck

<!-- Was verantwortet das Modul? Zwei Sätze. -->

## 2. Entitäten und Status

| Tabelle | Status | Übergänge |
|---|---|---|
| `__ENTITY_SNAKE__` | `ACTIVE` → `INACTIVE` | `deactivate` (nur aus `ACTIVE`, sonst 409) |

## 3. Service-Schnittstelle (für andere Module)

| Funktion | Zweck |
|---|---|
| `get___ENTITY_SNAKE__(session, id)` | Lesen, 404 wenn unbekannt |
| `list___MODULE__(session, limit, offset, status)` | Seite + Gesamtzahl |
| `create___ENTITY_SNAKE__(session, data, actor_id)` | Anlegen, 409 bei doppeltem Namen |
| `update___ENTITY_SNAKE__(session, id, data, actor_id)` | Stammdaten ändern |
| `deactivate___ENTITY_SNAKE__(session, id, actor_id)` | Statuswechsel unter Zeilensperre |

Alles andere im Modul ist intern.

## 4. Ereignisse

| Ereignis | Richtung | Payload |
|---|---|---|
| `__MODULE__.__ENTITY_SNAKE___deactivated` | meldet | `__ENTITY__Deactivated(id)` – wird erst gemeldet, wenn ein anderes Modul es verarbeitet |

## 5. HTTP (`/api/v1/__MODULE__`)

| Methode | Pfad | Antwort |
|---|---|---|
| GET | `` | `Page[__ENTITY__Out]`, Filter `?status=` |
| POST | `` | 201 `__ENTITY__Out` |
| GET | `/{id}` | `__ENTITY__Out` |
| PATCH | `/{id}` | `__ENTITY__Out` |
| POST | `/{id}/deactivate` | `__ENTITY__Out` |

Fehler: 404 `not_found`, 409 `conflict`, 422 `validation_error`.

## 6. Regeln und Ausnahmen

- Name ist eindeutig (`uq___ENTITY_SNAKE___name`), wird getrimmt, Vergleich beim Suchen case-insensitive.
