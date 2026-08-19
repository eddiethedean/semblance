"""CLI: serve, validate, fixture init, operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from semblance_foundry.app import FoundryMock
from semblance_foundry.config import FoundryMockConfig, TokenGrant
from semblance_foundry.fixtures.loaders import (
    apply_fixture,
    bundled_acme_path,
    load_fixture_file,
)
from semblance_foundry.registry import registered_operations
from semblance_foundry.state import FoundryState


def cmd_serve(args: argparse.Namespace) -> None:
    tokens = tuple(TokenGrant(token) for token in (args.token or []))
    if args.auth == "strict" and not tokens:
        raise SystemExit("strict auth requires at least one --token")
    config = FoundryMockConfig(seed=args.seed, auth=args.auth, tokens=tokens)
    mock = FoundryMock(config)
    mock.load_fixture(args.fixture or bundled_acme_path())
    app = mock.as_fastapi()
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn not found. Install semblance-foundry (pulls uvicorn via semblance)."
        ) from exc
    uvicorn.run(app, host=args.host, port=args.port)


def cmd_validate(args: argparse.Namespace) -> None:
    try:
        doc = load_fixture_file(args.fixture)
        apply_fixture(doc, FoundryState(seed=42))
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
        prog="semblance-foundry",
        description=(
            "Unofficial local Foundry API v2 ontology mock. "
            "Not affiliated with Palantir."
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
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--seed", type=int, default=42)
    serve.add_argument(
        "--auth",
        default="optional",
        choices=["disabled", "optional", "strict"],
    )
    serve.add_argument(
        "--token",
        action="append",
        default=[],
        help="Bearer token accepted in strict mode (repeatable)",
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
