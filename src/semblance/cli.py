"""
CLI for Semblance: run apps and export mocks.

Run a Semblance app with uvicorn, or export OpenAPI schema and JSON fixtures
for frontend integration. Use module:attr path (e.g. app:api or app:app).
"""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_app(path: str):
    """Load app from module:attr. If attr has as_fastapi(), it is called to get FastAPI app."""
    if ":" not in path:
        raise SystemExit(
            f"Invalid path {path!r}. Use module:attr (e.g. app:api or app:app)"
        )
    module_path, attr = path.split(":", 1)
    if not module_path or not attr:
        raise SystemExit("module:attr must both be non-empty")

    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.origin is None:
        raise SystemExit(f"Module {module_path!r} not found")

    loader = importlib.util.LazyLoader(spec.loader)  # type: ignore
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_path] = module
    spec.loader.exec_module(module)

    if not hasattr(module, attr):
        raise SystemExit(
            f"Attribute {attr!r} not found in module {module_path!r}"
        )

    app = getattr(module, attr)
    if hasattr(app, "as_fastapi"):
        app = app.as_fastapi()
    return app


def cmd_run(args: argparse.Namespace) -> None:
    """Run a Semblance app with uvicorn."""
    if args.reload:
        cmd = [
            sys.executable, "-m", "uvicorn",
            args.app,
            "--host", args.host,
            "--port", str(args.port),
            "--reload",
        ]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            raise SystemExit(
                "uvicorn not found. Install with: pip install uvicorn"
            )
    else:
        app = _load_app(args.app)
        try:
            import uvicorn
        except ImportError:
            raise SystemExit(
                "uvicorn not found. Install with: pip install uvicorn"
            )
        uvicorn.run(app, host=args.host, port=args.port)


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


def main() -> None:
    parser = argparse.ArgumentParser(prog="semblance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a Semblance app")
    run_parser.add_argument(
        "app",
        help="Module:attr path (e.g. app:api). If attr has as_fastapi(), it is called.",
    )
    run_parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    run_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    run_parser.add_argument("--reload", action="store_true", help="Enable reload")
    run_parser.set_defaults(func=cmd_run)

    export_parser = subparsers.add_parser("export", help="Export mocks")
    export_sub = export_parser.add_subparsers(dest="export_type", required=True)

    openapi_parser = export_sub.add_parser("openapi", help="Export OpenAPI schema")
    openapi_parser.add_argument("app", help="Module:attr path (e.g. app:api)")
    openapi_parser.add_argument("-o", "--output", help="Output file (- for stdout)")
    openapi_parser.add_argument("--examples", dest="include_examples", action="store_true")
    openapi_parser.set_defaults(func=cmd_export_openapi)

    fixtures_parser = export_sub.add_parser("fixtures", help="Export fixtures")
    fixtures_parser.add_argument("app", help="Module:attr path (e.g. app:api)")
    fixtures_parser.add_argument("-o", "--output", default="fixtures", help="Output directory")
    fixtures_parser.set_defaults(func=cmd_export_fixtures)

    args = parser.parse_args()
    if args.command == "run":
        cmd_run(args)
    elif args.command == "export":
        if args.export_type == "openapi":
            cmd_export_openapi(args)
        elif args.export_type == "fixtures":
            cmd_export_fixtures(args)


if __name__ == "__main__":
    main()
