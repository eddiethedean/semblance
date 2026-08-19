from pathlib import Path

import pytest

from semblance_databricks.fixtures.loaders import (
    apply_fixture,
    load_fixture_file,
    parse_fixture,
)
from semblance_databricks.state import DatabricksState


def test_acme_loads() -> None:
    from semblance_databricks.fixtures.loaders import bundled_acme_path

    doc = load_fixture_file(bundled_acme_path())
    state = DatabricksState(seed=42)
    apply_fixture(doc, state)
    assert len(state.clusters) >= 4
    assert len(state.jobs) >= 2
    assert "2001" in state.runs


def test_extra_fields_rejected() -> None:
    with pytest.raises(Exception):
        parse_fixture({"version": 1, "unknown": True})


def test_dangling_job_ref() -> None:
    doc = parse_fixture(
        {
            "version": 1,
            "runs": [{"run_id": "9", "job_id": "missing", "run_name": "x"}],
        }
    )
    with pytest.raises(ValueError, match="Dangling"):
        apply_fixture(doc, DatabricksState())


def test_duplicate_job_id() -> None:
    doc = parse_fixture(
        {
            "version": 1,
            "jobs": [
                {"job_id": "1", "name": "a"},
                {"job_id": "1", "name": "b"},
            ],
        }
    )
    with pytest.raises(ValueError, match="Duplicate"):
        apply_fixture(doc, DatabricksState())


def test_json_fixture(tmp_path: Path) -> None:
    path = tmp_path / "fix.json"
    path.write_text('{"version": 1, "clusters": []}', encoding="utf-8")
    doc = load_fixture_file(path)
    assert doc.version == 1
