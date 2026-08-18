from pathlib import Path

from semblance_foundry.cli import main


def test_validate_ok(capsys) -> None:
    from semblance_foundry.fixtures.loaders import bundled_acme_path

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
