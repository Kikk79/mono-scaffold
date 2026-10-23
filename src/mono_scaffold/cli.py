"""`mono` – Generator für modulare Monolithen.

    mono new <projekt>                 Grundgerüst anlegen (wie `ng new`)
    mono module <name> [--imports …]   Fachmodul anlegen und einhängen (wie `ng generate`)
    mono contracts                     Contracts aus docs/module-grenzen.md neu erzeugen

Die Abhängigkeitstabelle in `docs/module-grenzen.md` ist die Quelle der Wahrheit; die
Contracts in `pyproject.toml` werden daraus abgeleitet, nie von Hand gepflegt.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from importlib import resources
from pathlib import Path

RESERVED = {"core", "main", "jobs", "read_models", "modules", "tests", "app"}
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]*$")

MODULES_BEGIN = "<!-- mono:modules-begin -->"
MODULES_END = "<!-- mono:modules-end -->"
CONTRACTS_BEGIN = "# mono:contracts-begin"
CONTRACTS_END = "# mono:contracts-end"


class MonoError(Exception):
    """Benutzerfehler mit Handlungsanweisung."""


# ---------------------------------------------------------------- Vorlagen


def _templates() -> Path:
    return Path(str(resources.files("mono_scaffold") / "templates"))


def _render(text: str, tokens: dict[str, str]) -> str:
    for key, value in tokens.items():
        text = text.replace(key, value)
    return text


def _copy_tree(src: Path, dst: Path, tokens: dict[str, str]) -> list[Path]:
    """Kopiert eine Vorlage, ersetzt Tokens in Pfad und Inhalt. `dot_x` wird zu `.x`."""
    written: list[Path] = []
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        rel_parts = [
            _render(p.replace("dot_", ".", 1) if p.startswith("dot_") else p, tokens)
            for p in path.relative_to(src).parts
        ]
        target = dst.joinpath(*rel_parts)
        if target.exists():
            raise MonoError(f"Datei existiert schon: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_text(encoding="utf-8")
        target.write_text(_render(content, tokens), encoding="utf-8")
        if path.suffix == ".sh":
            target.chmod(0o755)
        written.append(target)
    return written


# ---------------------------------------------------------------- Projekt finden


def _find_project(start: Path) -> Path:
    """Projektwurzel = Verzeichnis mit `docs/module-grenzen.md` und `pyproject.toml`."""
    for candidate in [start, *start.parents]:
        if (candidate / "docs/module-grenzen.md").is_file() and (
            candidate / "pyproject.toml"
        ).is_file():
            return candidate
    raise MonoError(
        "Kein mono-Projekt gefunden (docs/module-grenzen.md + pyproject.toml). "
        "Im Projekt aufrufen oder --project angeben."
    )


# ---------------------------------------------------------------- Modultabelle


def read_modules(project: Path) -> list[tuple[str, str, list[str]]]:
    """Liest (name, verantwortung, erlaubte_importe) aus docs/module-grenzen.md."""
    text = (project / "docs/module-grenzen.md").read_text(encoding="utf-8")
    if MODULES_BEGIN not in text or MODULES_END not in text:
        raise MonoError("docs/module-grenzen.md: Marker mono:modules-begin/-end fehlen.")
    block = text.split(MODULES_BEGIN, 1)[1].split(MODULES_END, 1)[0]
    rows: list[tuple[str, str, list[str]]] = []
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-", " "} or cells[0] == "Modul":
            continue
        name = cells[0].strip("`")
        allowed = [m for m in re.findall(r"`([a-z][a-z0-9_]*)`", cells[2]) if m != "core"]
        rows.append((name, cells[1], allowed))
    return rows


def _add_module_row(project: Path, name: str, responsibility: str, allowed: list[str]) -> None:
    path = project / "docs/module-grenzen.md"
    text = path.read_text(encoding="utf-8")
    imports = ", ".join(f"`{m}`" for m in ["core", *allowed])
    row = f"| `{name}` | {responsibility} | {imports} |\n"
    text = text.replace(MODULES_END, row + MODULES_END, 1)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- Contracts


def _contract(
    cid: str, name: str, source: list[str], forbidden: list[str], ignore: list[str] | None = None
) -> str:
    lines = [
        "[[tool.importlinter.contracts]]",
        f'id = "{cid}"',
        f'name = "{name}"',
        'type = "forbidden"',
        "source_modules = [" + ", ".join(f'"{m}"' for m in source) + "]",
        "forbidden_modules = [",
        *[f'    "{m}",' for m in forbidden],
        "]",
        "allow_indirect_imports = true",
    ]
    if ignore:
        lines += ["ignore_imports = [", *[f'    "{m}",' for m in ignore], "]"]
    return "\n".join(lines) + "\n"


def build_contracts(modules: list[tuple[str, str, list[str]]]) -> str:
    """Erzeugt den Contract-Block aus der Modultabelle."""
    names = [m[0] for m in modules]
    infra = ["app.jobs", "app.main", "app.read_models"]
    out = [
        "# Erzeugt von `mono contracts` aus docs/module-grenzen.md. Nicht von Hand ändern.",
        _contract(
            "core",
            "core importiert kein Fachmodul",
            ["app.core"],
            ["app.modules", *infra],
            ignore=[f"app.core.model_registry -> app.modules.{m}.models" for m in names],
        ),
    ]
    for name, _resp, allowed in modules:
        unknown = sorted(set(allowed) - set(names))
        if unknown:
            raise MonoError(f"Modul `{name}` erlaubt unbekannte Module: {', '.join(unknown)}")
        forbidden = [f"app.modules.{m}" for m in names if m != name and m not in allowed]
        out.append(
            _contract(
                name,
                f"{name} importiert nur core" + (", " + ", ".join(allowed) if allowed else ""),
                [f"app.modules.{name}"],
                forbidden + infra,
            )
        )
        others = [f"app.modules.{m}" for m in names if m != name]
        out.append(
            _contract(
                f"{name}-repository-privat",
                f"Repository von {name} ist privat",
                others + ["app.read_models", "app.jobs"],
                [f"app.modules.{name}.repository"],
            )
        )
    if names:
        out.append(
            _contract(
                "read-models-nur-lesen",
                "read_models rufen keine Services",
                ["app.read_models"],
                [f"app.modules.{m}.service" for m in names],
            )
        )
    return "\n".join(out)


def write_contracts(project: Path) -> int:
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    if CONTRACTS_BEGIN not in text or CONTRACTS_END not in text:
        raise MonoError("pyproject.toml: Marker mono:contracts-begin/-end fehlen.")
    modules = read_modules(project)
    head, rest = text.split(CONTRACTS_BEGIN, 1)
    _old, tail = rest.split(CONTRACTS_END, 1)
    block = build_contracts(modules)
    path.write_text(f"{head}{CONTRACTS_BEGIN}\n{block}\n{CONTRACTS_END}{tail}", encoding="utf-8")
    return len(modules)


# ---------------------------------------------------------------- Marker-Blöcke


def _add_to_block(
    path: Path, begin: str, end: str, lines: list[str], *, imports: bool = False
) -> None:
    """Fügt Zeilen in den Block zwischen zwei Markern ein und hält ihn sortiert.

    Import-Blöcke bekommen vor dem End-Marker eine Leerzeile, so wie ruffs isort (I001) es
    nach einem Import-Block verlangt.
    """
    text = path.read_text(encoding="utf-8")
    if begin not in text or end not in text:
        raise MonoError(f"{path}: Marker `{begin}`/`{end}` fehlen.")
    head, rest = text.split(begin, 1)
    block, tail = rest.split(end, 1)
    existing = [ln for ln in block.splitlines() if ln.strip()]
    merged = sorted(set(existing) | set(lines), key=_import_sort_key)
    if not merged:
        body = "\n"
    else:
        body = "\n" + "\n".join(merged) + ("\n\n" if imports else "\n")
    path.write_text(f"{head}{begin}{body}{end}{tail}", encoding="utf-8")


def _import_sort_key(line: str) -> tuple[str, str]:
    """isort-Reihenfolge: nach Modulpfad, `from a import` vor `from a.b import`."""
    m = re.match(r"\s*from\s+(\S+)\s+import", line)
    return (m.group(1) if m else line, line)


# ---------------------------------------------------------------- Befehle


def _pascal(snake: str) -> str:
    return "".join(part.capitalize() for part in snake.split("_"))


def _snake(pascal: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", pascal).lower()


def _default_entity(module: str) -> str:
    singular = (
        module[:-1]
        if module.endswith("s") and not module.endswith("ss") and len(module) > 3
        else module
    )
    return _pascal(singular)


def cmd_new(args: argparse.Namespace) -> int:
    name: str = args.name
    if not PROJECT_RE.match(name):
        raise MonoError("Projektname: Kleinbuchstaben, Ziffern, Bindestrich (z. B. silatec-erp).")
    target = Path(args.dir or name).resolve()
    if target.exists() and any(target.iterdir()):
        raise MonoError(f"Zielverzeichnis ist nicht leer: {target}")
    tokens = {
        "__PROJECT__": name,
        "__PROJECT_SNAKE__": name.replace("-", "_"),
        "__TITLE__": args.title or _pascal(name.replace("-", "_")).replace("Erp", "ERP"),
        "__DATE__": date.today().isoformat(),
    }
    written = _copy_tree(_templates() / "project", target, tokens)
    shutil.copyfile(target / ".env.example", target / ".env")
    write_contracts(target)
    if shutil.which("git") and not (target / ".git").exists():
        subprocess.run(["git", "init", "-q", str(target)], check=False)
    print(f"Projekt `{name}` angelegt: {target} ({len(written) + 1} Dateien)")
    print(
        "\nNächste Schritte:\n"
        f"  cd {target}\n"
        "  docker compose up -d postgres      # oder eigenen Postgres in .env eintragen\n"
        "  uv sync\n"
        "  bash scripts/check.sh               # Windows: scripts/check.ps1\n"
        "  mono module auth --entity User     # erstes Fachmodul\n"
        "  uv run uvicorn app.main:app --reload\n"
        "\nArbeitsregeln für den Coding-Agent: CLAUDE.md, docs/module-grenzen.md, "
        "docs/conventions/coding.md"
    )
    return 0


def cmd_module(args: argparse.Namespace) -> int:
    name: str = args.name
    if not NAME_RE.match(name) or name in RESERVED:
        raise MonoError("Modulname: snake_case, nicht reserviert (core, main, jobs, read_models).")
    project = _find_project(Path(args.project).resolve() if args.project else Path.cwd())
    modules = read_modules(project)
    names = [m[0] for m in modules]
    if name in names or (project / "app/modules" / name).exists():
        raise MonoError(f"Modul `{name}` gibt es schon.")
    allowed = [
        m.strip() for m in (args.imports or "").split(",") if m.strip() and m.strip() != "core"
    ]
    unknown = sorted(set(allowed) - set(names))
    if unknown:
        raise MonoError(
            f"--imports nennt unbekannte Module: {', '.join(unknown)} "
            f"(vorhanden: {', '.join(names) or '–'})"
        )
    entity = args.entity or _default_entity(name)
    if not re.match(r"^[A-Z][A-Za-z0-9]*$", entity):
        raise MonoError("--entity muss PascalCase sein (z. B. Partner).")
    tokens = {
        "__MODULE__": name,
        "__MODULE_TITLE__": _pascal(name),
        "__ENTITY__": entity,
        "__ENTITY_SNAKE__": _snake(entity),
        "__DATE__": date.today().isoformat(),
        "__IMPORTS__": ", ".join(["core", *allowed]),
    }
    written = _copy_tree(_templates() / "module", project, tokens)
    _add_module_row(project, name, args.responsibility or f"{entity}-Stammdaten", allowed)
    _add_to_block(
        project / "app/main.py",
        "# mono:imports-begin",
        "# mono:imports-end",
        [
            f"from app.modules.{name} import events as _{name}_events  # noqa: F401",
            f"from app.modules.{name}.router import router as {name}_router",
        ],
        imports=True,
    )
    _add_to_block(
        project / "app/main.py",
        "# mono:include-begin",
        "# mono:include-end",
        [f"app.include_router({name}_router)"],
    )
    _add_to_block(
        project / "app/core/model_registry.py",
        "# mono:models-begin",
        "# mono:models-end",
        [f"from app.modules.{name} import models as _{name}_models  # noqa: F401"],
        imports=True,
    )
    count = write_contracts(project)
    print(
        f"Modul `{name}` (Entität {entity}) angelegt, {len(written)} Dateien, "
        f"{count} Module in den Contracts."
    )
    print(
        "\nNächste Schritte:\n"
        f'  uv run alembic revision --autogenerate -m "{name}"   # prüfen, dann upgrade head\n'
        "  bash scripts/check.sh\n"
        f"  docs/interfaces/{name}.md ausfüllen, Fachlogik in app/modules/{name}/service.py"
    )
    return 0


def cmd_contracts(args: argparse.Namespace) -> int:
    project = _find_project(Path(args.project).resolve() if args.project else Path.cwd())
    count = write_contracts(project)
    print(f"Contracts neu erzeugt für {count} Module: {project / 'pyproject.toml'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mono", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="Grundgerüst anlegen")
    p_new.add_argument("name", help="Projektname in kebab-case, z. B. silatec-erp")
    p_new.add_argument("--dir", help="Zielverzeichnis (Standard: ./<name>)")
    p_new.add_argument("--title", help="Anzeigename, z. B. 'Silatec ERP'")
    p_new.set_defaults(func=cmd_new)

    p_mod = sub.add_parser("module", help="Fachmodul anlegen und einhängen")
    p_mod.add_argument("name", help="Modulname in snake_case, z. B. partners")
    p_mod.add_argument(
        "--entity", help="Name der Hauptentität in PascalCase (Standard: aus dem Modulnamen)"
    )
    p_mod.add_argument(
        "--imports",
        help="Erlaubte Module, kommagetrennt, z. B. partners,catalog (core ist immer erlaubt)",
    )
    p_mod.add_argument("--responsibility", help="Kurztext für die Modultabelle")
    p_mod.add_argument("--project", help="Projektwurzel (Standard: aktuelles Verzeichnis)")
    p_mod.set_defaults(func=cmd_module)

    p_con = sub.add_parser(
        "contracts", help="import-linter-Contracts aus der Modultabelle neu erzeugen"
    )
    p_con.add_argument("--project", help="Projektwurzel")
    p_con.set_defaults(func=cmd_contracts)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MonoError as exc:
        print(f"mono: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
