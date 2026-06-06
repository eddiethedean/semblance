"""Tests for config loading and SemblanceAPI.from_config."""

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


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "nonexistent.yaml")
    assert cfg.seed is None
    assert cfg.stateful is False


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
