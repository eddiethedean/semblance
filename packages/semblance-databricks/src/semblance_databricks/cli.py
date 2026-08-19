"""CLI: serve, validate, fixture init, operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from semblance_databricks.app import DatabricksMock
from semblance_databricks.config import DatabricksMockConfig
from semblance_databricks.fixtures.loaders import bundled_acme_path, load_fixture_file
from semblance_databricks.registry import registered_operations


def cmd_serve(args: argparse.Namespace) -> None:
    config = DatabricksMockConfig(seed=args.seed, auth=args.auth)
    mock = DatabricksMock(config)
    mock.load_fixture(args.fixture or bundled_acme_path())
    app = mock.as_fastapi()
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn not found. Install semblance (pulls uvicorn)."
        ) from exc
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_validate(args: argparse.Namespace) -> None:
    try:
        load_fixture_file(args.fixture)
    except Exception as exc:
        raise SystemExit(f"Invalid fixture: {exc}") from exc
    print("OK")


def cmd_fixture_init(args: argparse.Namespace) -> None:
    dest = Path(args.output)
    if dest.exists() and not args.force:
        raise SystemExit(f"{dest} already exists (use --force to overwrite)")
    dest.write_text(bundled_acme_path().read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {dest}")


def cmd_operations(_args: argparse.Namespace) -> None:
    rows = registered_operations()
    width = max((len(op.operation_id) for op in rows), default=8)
    print(f"{'operation':<{width}}  {'level':<16}  method  path")
    for op in rows:
        print(
            f"{op.operation_id:<{width}}  {op.support_level:<16}  "
            f"{op.method:<6}  {op.path}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semblance-databricks",
        description=(
            "Unofficial local Databricks workspace REST mock. "
            "Not affiliated with Databricks."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run a local mock server")
    serve.add_argument(
        "--fixture",
        default=None,
        help="YAML or JSON fixture path (default: bundled acme example)",
    )
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8766)
    serve.add_argument("--seed", type=int, default=42)
    serve.add_argument(
        "--auth",
        default="optional",
        choices=["disabled", "optional", "strict"],
    )
    serve.set_defaults(func=cmd_serve)

    validate = sub.add_parser("validate", help="Validate a fixture without serving")
    validate.add_argument("fixture")
    validate.set_defaults(func=cmd_validate)

    init = sub.add_parser("fixture", help="Fixture helpers")
    init_sub = init.add_subparsers(dest="fixture_command", required=True)
    init_cmd = init_sub.add_parser("init", help="Write the bundled example fixture")
    init_cmd.add_argument("--output", required=True)
    init_cmd.add_argument("--force", action="store_true")
    init_cmd.set_defaults(func=cmd_fixture_init)

    ops = sub.add_parser("operations", help="Print the compatibility table")
    ops.set_defaults(func=cmd_operations)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
