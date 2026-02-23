"""
Optional config loading for SemblanceAPI defaults.

Load from [tool.semblance] in pyproject.toml or from semblance.yaml.
Used when constructing SemblanceAPI with config_path= or from_config().
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass
class SemblanceConfig:
    """Default options for SemblanceAPI. All fields optional with None/defaults."""

    seed: int | None = None
    stateful: bool = False
    validate_responses: bool = False
    validate_links: bool = False
    verbose_errors: bool = False
    list_count: int = 5


_DEFAULT = SemblanceConfig()


def _load_toml_section(path: Path) -> dict | None:
    """Load [tool.semblance] from a TOML file. Returns None if not found or on error."""
    try:
        with open(path, "rb") as f:
            data = _toml_load(f)
    except Exception:
        return None
    tool = data.get("tool")
    if not isinstance(tool, dict):
        return None
    return tool.get("semblance") if isinstance(tool.get("semblance"), dict) else None


def _toml_load(f: object) -> dict[str, object]:
    """Load TOML; use tomllib (3.11+) or tomli."""
    try:
        import tomllib  # type: ignore[import-not-found]

        return cast(dict[str, object], tomllib.load(f))
    except ImportError:
        import tomli

        return cast(dict[str, object], tomli.load(f))  # type: ignore[arg-type]


def _load_yaml(path: Path) -> dict | None:
    """Load YAML file. Returns None if pyyaml not installed or on error."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _merge_config(config_dict: dict | None) -> SemblanceConfig:
    """Build SemblanceConfig from a dict; missing keys use defaults."""
    if not config_dict:
        return _DEFAULT
    seed = config_dict.get("seed")
    return SemblanceConfig(
        seed=seed if seed is not None else _DEFAULT.seed,
        stateful=config_dict.get("stateful", _DEFAULT.stateful),
        validate_responses=config_dict.get(
            "validate_responses", _DEFAULT.validate_responses
        ),
        validate_links=config_dict.get("validate_links", _DEFAULT.validate_links),
        verbose_errors=config_dict.get("verbose_errors", _DEFAULT.verbose_errors),
        list_count=config_dict.get("list_count", _DEFAULT.list_count),
    )


def load_config(config_path: str | Path | None = None) -> SemblanceConfig:
    """
    Load Semblance config from a file or by discovery.

    If config_path is given, load from that file (.yaml/.yml or .toml).
    If config_path is None, look for semblance.yaml or pyproject.toml in the
    current working directory and one level up.

    Returns SemblanceConfig with defaults for any missing keys.
    """
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            return _DEFAULT
        if path.suffix in (".yaml", ".yml"):
            data = _load_yaml(path)
            return _merge_config(data)
        if path.suffix == ".toml" or path.name == "pyproject.toml":
            data = _load_toml_section(path)
            return _merge_config(data)
        return _DEFAULT

    # Discovery: cwd and parent
    for directory in (Path.cwd(), Path.cwd().parent):
        yaml_path = directory / "semblance.yaml"
        if yaml_path.exists():
            data = _load_yaml(yaml_path)
            return _merge_config(data)
        yml_path = directory / "semblance.yml"
        if yml_path.exists():
            data = _load_yaml(yml_path)
            return _merge_config(data)
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            data = _load_toml_section(pyproject)
            if data is not None:
                return _merge_config(data)
    return _DEFAULT
