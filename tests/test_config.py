"""Tests for config loading and SemblanceAPI.from_config."""

import sys

import pytest

from semblance import SemblanceAPI
from semblance.config import load_config
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


def test_load_config_from_yaml(tmp_path):
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 99\nvalidate_responses: true\n")
    cfg = load_config(yaml_path)
    assert cfg.seed == 99
    assert cfg.validate_responses is True


def test_load_config_from_pyproject_toml(tmp_path):
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text(
        '[project]\nname = "test"\n\n[tool.semblance]\nseed = 42\nstateful = true\n'
    )
    cfg = load_config(toml_path)
    assert cfg.seed == 42
    assert cfg.stateful is True


def test_toml_config_loads_with_standard_library_parser(tmp_path, monkeypatch):
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.semblance]\nseed = 17\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "tomli", None)

    cfg = load_config(toml_path)

    assert cfg.seed == 17


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.yaml")
    assert cfg.seed is None
    assert cfg.stateful is False


@pytest.mark.parametrize(
    "source", ["missing", "empty", "invalid", "unknown", "discovery"]
)
def test_default_config_mutation_does_not_affect_other_loads(
    tmp_path, monkeypatch, source
):
    config_path = tmp_path / "missing.yaml"
    if source == "empty":
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
    elif source == "invalid":
        config_path = tmp_path / "invalid.toml"
        config_path.write_text("[invalid")
    elif source == "unknown":
        config_path = tmp_path / "config.txt"
        config_path.write_text("ignored")
    elif source == "discovery":
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)
        config_path = None

    first = load_config(config_path)
    monkeypatch.setattr(first, "list_count", 99)

    assert load_config(config_path).list_count == 5
    partial = tmp_path / "partial.toml"
    partial.write_text("[tool.semblance]\nseed = 7\n")
    assert load_config(partial).list_count == 5


@pytest.mark.parametrize(
    ("option", "attribute"),
    [
        ("stateful", "_store"),
        ("validate_responses", "_validate_responses"),
        ("validate_links", "_validate_links"),
        ("verbose_errors", "_verbose_errors"),
    ],
)
def test_explicit_false_overrides_enabled_config(tmp_path, option, attribute):
    config_path = tmp_path / "pyproject.toml"
    config_path.write_text(f"[tool.semblance]\n{option} = true\n")

    inherited = SemblanceAPI(config_path=str(config_path))
    overridden = SemblanceAPI(config_path=str(config_path), **{option: False})

    if option == "stateful":
        assert inherited._store is not None
        assert overridden._store is None
    else:
        assert getattr(inherited, attribute) is True
        assert getattr(overridden, attribute) is False


def test_load_config_discovery_from_cwd(tmp_path, monkeypatch):
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 77\n")
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None)
    assert cfg.seed == 77


def test_semblance_api_uses_config_path(tmp_path):
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 123\nvalidate_responses: true\n")
    api = SemblanceAPI(config_path=str(yaml_path))
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    client = make_client(api.as_fastapi())
    r1 = client.get("/users?name=a")
    r2 = client.get("/users?name=a")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()


def test_semblance_api_from_config(tmp_path):
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 456\n")
    api = SemblanceAPI.from_config(str(yaml_path))
    api.get("/items", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/items?name=x").status_code == 200


def test_semblance_api_from_config_keyword_overrides(tmp_path):
    yaml_path = tmp_path / "semblance.yaml"
    yaml_path.write_text("seed: 1\n")
    api = SemblanceAPI.from_config(str(yaml_path), seed=999)
    api.get("/users", input=UserQuery, output=list[User], list_count=2)(lambda: None)
    client = make_client(api.as_fastapi())
    r1 = client.get("/users?name=a")
    r2 = client.get("/users?name=b")
    assert [x["created_at"] for x in r1.json()] == [x["created_at"] for x in r2.json()]
