from pathlib import Path

import pytest

from semblance_foundry.fixtures.loaders import (
    apply_fixture,
    load_fixture_file,
    parse_fixture,
)
from semblance_foundry.state import FoundryState


def test_rejects_unknown_fields() -> None:
    with pytest.raises(Exception):
        parse_fixture({"version": 1, "ontologies": [], "nope": True})


def test_rejects_duplicate_primary_key(tmp_path: Path) -> None:
    path = tmp_path / "dup.yaml"
    path.write_text(
        """
version: 1
ontologies:
  - apiName: acme
    objectTypes:
      - apiName: Employee
        primaryKey: employeeId
        objects:
          - employeeId: "1"
            name: A
          - employeeId: "1"
            name: B
""",
        encoding="utf-8",
    )
    doc = load_fixture_file(path)
    state = FoundryState(seed=1)
    with pytest.raises(ValueError, match="Duplicate primary key"):
        apply_fixture(doc, state)


def test_rejects_wrong_version() -> None:
    with pytest.raises(Exception):
        parse_fixture({"version": 2, "ontologies": []})


def test_load_bundled_fixture() -> None:
    from semblance_foundry import FoundryMock

    foundry = FoundryMock()
    foundry.load_bundled_fixture()
    assert "acme" in foundry.state.ontologies
    with pytest.raises(ValueError, match="unknown bundled fixture"):
        foundry.load_bundled_fixture("nope")


def test_failed_reload_preserves_state_callbacks_and_mutation_facade(
    tmp_path: Path,
) -> None:
    from semblance_foundry import FoundryMock

    foundry = FoundryMock().load_bundled_fixture()

    def callback(*_: object) -> dict[str, int]:
        return {"value": 1}

    foundry.register_query("query", callback)
    old_state = foundry.state
    old_ontologies = foundry.ontologies

    with pytest.raises(FileNotFoundError):
        foundry.load_fixture(tmp_path / "missing.yaml")

    assert foundry.state is old_state
    assert foundry.ontologies is old_ontologies
    assert foundry.state.ontologies
    assert foundry.state.query_callbacks["query"] is callback

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("version: 1\nontologies: [invalid]\n", encoding="utf-8")
    with pytest.raises(Exception):
        foundry.load_fixture(invalid)

    assert foundry.state is old_state
    assert foundry.ontologies is old_ontologies
    assert foundry.state.ontologies

    invalid_link = tmp_path / "invalid-link.yaml"
    invalid_link.write_text(
        """
version: 1
ontologies:
  - apiName: partial
    linkTypes:
      - apiName: broken
        from: Missing
        to: AlsoMissing
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not defined"):
        foundry.load_fixture(invalid_link)

    assert foundry.state is old_state
    assert foundry.ontologies is old_ontologies
    assert "partial" not in foundry.state.ontologies

    foundry.ontologies.add_objects(
        "acme", "Employee", [{"employeeId": "added", "name": "Added"}]
    )
    assert foundry.state.get_object("acme", "Employee", "added") is not None


def test_successful_reload_keeps_retained_mutation_facade_live() -> None:
    from fastapi.testclient import TestClient

    from semblance_foundry import FoundryMock

    foundry = FoundryMock().load_bundled_fixture()
    mutations = foundry.ontologies
    client = TestClient(foundry.as_fastapi())

    foundry.load_bundled_fixture()
    mutations.add_objects(
        "acme", "Employee", [{"employeeId": "after-reload", "name": "Live"}]
    )

    response = client.get("/api/v2/ontologies/acme/objects/Employee/after-reload")
    assert response.status_code == 200
