from pathlib import Path

from semblance_databricks.cli import main


def test_validate_ok(capsys) -> None:
    from semblance_databricks.fixtures.loaders import bundled_acme_path

    main(["validate", str(bundled_acme_path())])
    assert capsys.readouterr().out.strip() == "OK"


def test_operations_lists_rows(capsys) -> None:
    main(["operations"])
    out = capsys.readouterr().out
    assert "ListClusters" in out
    assert "PermanentDeleteCluster" in out


def test_fixture_init(tmp_path: Path) -> None:
    dest = tmp_path / "databricks.yaml"
    main(["fixture", "init", "--output", str(dest)])
    assert dest.exists()
    assert "ingest-1" in dest.read_text(encoding="utf-8")


def test_serve_defaults_to_bundled_fixture() -> None:
    from semblance_databricks.cli import build_parser

    args = build_parser().parse_args(["serve"])
    assert args.fixture is None
    assert args.port == 8766
