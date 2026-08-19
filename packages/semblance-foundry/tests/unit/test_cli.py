from pathlib import Path

import pytest

from semblance_foundry.cli import main
from semblance_foundry.fixtures.loaders import bundled_acme_path


def test_validate_ok(capsys) -> None:
    main(["validate", str(bundled_acme_path())])
    assert capsys.readouterr().out.strip() == "OK"


def test_operations_lists_rows(capsys) -> None:
    main(["operations"])
    out = capsys.readouterr().out
    assert "ListOntologies" in out
    assert "ApplyAction" in out


def test_fixture_init(tmp_path: Path) -> None:
    dest = tmp_path / "foundry.yaml"
    main(["fixture", "init", "--output", str(dest)])
    assert dest.exists()
    assert "apiName: acme" in dest.read_text(encoding="utf-8")


def test_serve_defaults_to_bundled_fixture() -> None:
    from semblance_foundry.cli import build_parser

    args = build_parser().parse_args(["serve"])
    assert args.fixture is None
    assert args.port == 8765


def test_serve_strict_requires_token() -> None:
    from semblance_foundry.cli import build_parser

    args = build_parser().parse_args(["serve", "--auth", "strict", "--token", "t"])
    assert args.token == ["t"]


def test_validate_rejects_dangling_link(tmp_path: Path) -> None:
    dest = tmp_path / "bad.yaml"
    dest.write_text(
        bundled_acme_path()
        .read_text(encoding="utf-8")
        .replace("to: hq", "to: missing-office"),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="Invalid fixture"):
        main(["validate", str(dest)])
