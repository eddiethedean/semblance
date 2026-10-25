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


def test_failed_reload_preserves_state_and_callbacks(tmp_path: Path) -> None:
    from semblance_databricks import DatabricksMock

    mock = DatabricksMock().load_bundled_fixture()

    def callback(*_: object) -> dict[str, list[list[str]]]:
        return {"data_array": [["ok"]]}

    mock.register_statement("select 1", callback)
    old_state = mock.state

    with pytest.raises(FileNotFoundError):
        mock.load_fixture(tmp_path / "missing.yaml")

    assert mock.state is old_state
    assert mock.state.jobs
    assert mock.state.statement_callbacks["select 1"] is callback

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("version: 1\njobs: [invalid]\n", encoding="utf-8")
    with pytest.raises(Exception):
        mock.load_fixture(invalid)

    assert mock.state is old_state
    assert mock.state.jobs

    partially_applied = tmp_path / "duplicate-jobs.yaml"
    partially_applied.write_text(
        """
version: 1
jobs:
  - job_id: duplicate
    name: first
  - job_id: duplicate
    name: second
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate job_id"):
        mock.load_fixture(partially_applied)

    assert mock.state is old_state
    assert mock.state.jobs
    assert "duplicate" not in mock.state.jobs


def test_successful_reload_preserves_custom_user() -> None:
    from fastapi.testclient import TestClient

    from semblance_databricks import DatabricksMock

    mock = DatabricksMock().load_bundled_fixture()
    mock.state.user["userName"] = "custom@example.com"
    client = TestClient(mock.as_fastapi())

    mock.load_bundled_fixture()

    response = client.get("/api/2.0/preview/scim/v2/Me")
    assert response.json()["userName"] == "custom@example.com"
