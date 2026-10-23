# Interfaces

Eine Datei je Fachmodul, `docs/interfaces/<modul>.md`, bindend für das Modul. `mono module` legt sie an; der Owner des Moduls füllt sie.

Inhalt je Datei:

1. **Zweck** – was das Modul verantwortet, in zwei Sätzen.
2. **Entitäten und Status** – Tabellen, Statuswerte, Übergänge (wer darf welchen auslösen).
3. **Service-Schnittstelle** – die öffentlichen Funktionen in `service.py`, die andere Module rufen dürfen; alles andere ist intern.
4. **Ereignisse** – was das Modul meldet (`<modul>.<ereignis>`, Payload) und was es verarbeitet.
5. **HTTP** – Endpunkte unter `/api/v1/<modul>`, Rollen, Fehlercodes.
6. **Regeln und Ausnahmen** – fachliche Invarianten, bewusste Abweichungen von den Konventionen mit Grund.
