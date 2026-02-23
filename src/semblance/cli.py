"""
CLI for Semblance: run apps and export mocks.

Run a Semblance app with uvicorn, or export OpenAPI schema and JSON fixtures
for frontend integration. Use module or module:attr (e.g. app:api or app).
"""

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any


def _resolve_app_path(path: str) -> str:
    """If path contains ':', return as-is. Else infer module:attr (single SemblanceAPI or FastAPI in module)."""
    if ":" in path:
        return path
    module_path = path
    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.origin is None:
        raise SystemExit(f"Module {module_path!r} not found")
    if spec.loader is None:
        raise SystemExit(
            f"Module {module_path!r} cannot be loaded (e.g. namespace package)"
        )
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = module
    spec.loader.exec_module(module)
    try:
        from fastapi import FastAPI as _FastAPI  # noqa: N806
    except ImportError:
        _FastAPI = None  # type: ignore[assignment,misc]  # noqa: N806
    candidates = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if hasattr(obj, "as_fastapi"):
            candidates.append(name)
        elif _FastAPI is not None and isinstance(obj, _FastAPI):
            candidates.append(name)
    if len(candidates) == 0:
        raise SystemExit(
            f"No SemblanceAPI or FastAPI found in module {module_path!r}. "
            "Use module:attr (e.g. app:api or app:app)."
        )
    if len(candidates) > 1:
        raise SystemExit(
            f"Multiple app candidates in {module_path!r}: {candidates}. "
            "Use module:attr to specify (e.g. app:api)."
        )
    return f"{module_path}:{candidates[0]}"


def _load_target(path: str) -> Any:
    """Load module:attr and return the raw object (SemblanceAPI or FastAPI), without calling as_fastapi()."""
    resolved = _resolve_app_path(path)
    if ":" not in resolved:
        raise SystemExit("module:attr must both be non-empty")
    module_path, attr = resolved.split(":", 1)
    if not module_path or not attr:
        raise SystemExit("module:attr must both be non-empty")
    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.origin is None:
        raise SystemExit(f"Module {module_path!r} not found")
    if spec.loader is None:
        raise SystemExit(
            f"Module {module_path!r} cannot be loaded (e.g. namespace package)"
        )
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = module
    spec.loader.exec_module(module)
    if not hasattr(module, attr):
        raise SystemExit(f"Attribute {attr!r} not found in module {module_path!r}")
    return getattr(module, attr)


def _load_app(path: str) -> Any:
    """Load app from module or module:attr. If attr has as_fastapi(), it is called to get FastAPI app."""
    target = _load_target(path)
    if hasattr(target, "as_fastapi"):
        return target.as_fastapi()
    return target


def cmd_run(args: argparse.Namespace) -> None:
    """Run a Semblance app with uvicorn."""
    app = _load_app(args.app)
    try:
        import uvicorn
    except ImportError:
        raise SystemExit("uvicorn not found. Install with: pip install uvicorn")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


def cmd_export_openapi(args: argparse.Namespace) -> None:
    """Export OpenAPI schema."""
    import json

    from fastapi import FastAPI

    from semblance.export import export_openapi

    app = _load_app(args.app)
    if not isinstance(app, FastAPI):
        raise SystemExit("App must be a FastAPI instance")
    schema = export_openapi(app, include_examples=args.include_examples)
    output = args.output or "-"
    if output == "-":
        print(json.dumps(schema, indent=2))
    else:
        Path(output).write_text(json.dumps(schema, indent=2))
        print(f"Wrote {output}")


def cmd_export_fixtures(args: argparse.Namespace) -> None:
    """Export JSON fixtures per endpoint."""
    from fastapi import FastAPI

    from semblance.export import export_fixtures

    app = _load_app(args.app)
    if not isinstance(app, FastAPI):
        raise SystemExit("App must be a FastAPI instance")
    output_dir = Path(args.output or "fixtures")
    export_fixtures(app, output_dir)
    print(f"Wrote fixtures to {output_dir}")


INIT_APP_PY = '''"""
Minimal Semblance API. Run: semblance run app:api --port 8000
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel
from semblance import DateRangeFrom, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]


api = SemblanceAPI(seed=42)


@api.get("/users", input=UserQuery, output=list[User], list_count=2)
def users():
    pass


app = api.as_fastapi()
'''

INIT_SEMBLANCE_YAML = """# Optional Semblance defaults (used by semblance run when no args override)
# seed: 42
# stateful: false
# validate_responses: false
"""


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold a minimal runnable Semblance app (app.py and optional semblance.yaml)."""
    cwd = Path.cwd()
    app_py = cwd / "app.py"
    if app_py.exists() and not getattr(args, "force", False):
        print("app.py already exists. Use --force to overwrite.", file=sys.stderr)
        raise SystemExit(1)
    app_py.write_text(INIT_APP_PY, encoding="utf-8")
    print(f"Wrote {app_py}")
    if getattr(args, "with_config", False):
        config_path = cwd / "semblance.yaml"
        config_path.write_text(INIT_SEMBLANCE_YAML, encoding="utf-8")
        print(f"Wrote {config_path}")
    print("Run: semblance run app:api --port 8000", file=sys.stderr)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate routes and link bindings without starting a server. Exit 0 if valid, 1 otherwise."""
    from semblance.validation import get_duplicate_endpoint_errors, validate_specs

    target = _load_target(args.app)
    if not hasattr(target, "get_endpoint_specs"):
        raise SystemExit(
            "Validate requires a SemblanceAPI (module:attr with get_endpoint_specs). "
            "FastAPI apps cannot be validated."
        )
    specs = target.get_endpoint_specs()
    errors = validate_specs(specs) + get_duplicate_endpoint_errors(specs)
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        raise SystemExit(1)
    print("OK", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(prog="semblance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run a Semblance app",
        description="Run a Semblance or FastAPI app. Examples: semblance run app:api --port 8000",
    )
    run_parser.add_argument(
        "app",
        help="Module or module:attr (e.g. app:api or app). If only module, api or app is inferred when unambiguous.",
    )
    run_parser.add_argument(
        "--host", default="127.0.0.1", help="Host (default: 127.0.0.1)"
    )
    run_parser.add_argument(
        "--port", type=int, default=8000, help="Port (default: 8000)"
    )
    run_parser.add_argument("--reload", action="store_true", help="Enable reload")
    run_parser.set_defaults(func=cmd_run)

    export_parser = subparsers.add_parser("export", help="Export mocks")
    export_sub = export_parser.add_subparsers(dest="export_type", required=True)

    openapi_parser = export_sub.add_parser("openapi", help="Export OpenAPI schema")
    openapi_parser.add_argument(
        "app",
        help="Module or module:attr (e.g. app:api or app).",
    )
    openapi_parser.add_argument("-o", "--output", help="Output file (- for stdout)")
    openapi_parser.add_argument(
        "--examples", dest="include_examples", action="store_true"
    )
    openapi_parser.set_defaults(func=cmd_export_openapi)

    fixtures_parser = export_sub.add_parser("fixtures", help="Export fixtures")
    fixtures_parser.add_argument(
        "app",
        help="Module or module:attr (e.g. app:api or app).",
    )
    fixtures_parser.add_argument(
        "-o", "--output", default="fixtures", help="Output directory"
    )
    fixtures_parser.set_defaults(func=cmd_export_fixtures)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate routes and link bindings without starting a server",
    )
    validate_parser.add_argument(
        "app",
        help="Module or module:attr (e.g. app:api). Must be a SemblanceAPI.",
    )
    validate_parser.set_defaults(func=cmd_validate)

    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold a minimal runnable Semblance app (app.py and optional semblance.yaml)",
    )
    init_parser.add_argument(
        "-c",
        "--with-config",
        action="store_true",
        help="Also write semblance.yaml with commented defaults",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite app.py if it already exists",
    )
    init_parser.set_defaults(func=cmd_init)

    args = parser.parse_args()
    if args.command == "run":
        cmd_run(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "export":
        if args.export_type == "openapi":
            cmd_export_openapi(args)
        elif args.export_type == "fixtures":
            cmd_export_fixtures(args)
    elif args.command == "validate":
        cmd_validate(args)


if __name__ == "__main__":
    main()
