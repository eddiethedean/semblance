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
