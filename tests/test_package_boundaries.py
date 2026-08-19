"""Lock adapter import graphs: no cross-adapter or private core imports."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDRY_SRC = ROOT / "packages" / "semblance-foundry" / "src"
DATABRICKS_SRC = ROOT / "packages" / "semblance-databricks" / "src"


def _skip_part(part: str) -> bool:
    return part.startswith("semblance_foundry-") or part.startswith(
        "semblance_databricks-"
    )


def _py_files(src: Path) -> list[Path]:
    return [p for p in src.rglob("*.py") if not any(_skip_part(x) for x in p.parts)]


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _is_pkg(mod: str, pkg: str) -> bool:
    return mod == pkg or mod.startswith(pkg + ".")


def _private_semblance(mod: str) -> bool:
    parts = mod.split(".")
    if parts[0] != "semblance":
        return False
    return any(part.startswith("_") for part in parts[1:])


def _violations(src: Path, *, forbidden_adapter: str) -> list[str]:
    found: list[str] = []
    for path in _py_files(src):
        rel = path.relative_to(ROOT)
        for mod in _imported_modules(path):
            if _is_pkg(mod, forbidden_adapter):
                found.append(f"{rel}: imports {mod}")
            if _private_semblance(mod):
                found.append(f"{rel}: imports private {mod}")
    return found


def test_foundry_does_not_import_databricks_or_private_semblance() -> None:
    assert _violations(FOUNDRY_SRC, forbidden_adapter="semblance_databricks") == []


def test_databricks_does_not_import_foundry_or_private_semblance() -> None:
    assert _violations(DATABRICKS_SRC, forbidden_adapter="semblance_foundry") == []
