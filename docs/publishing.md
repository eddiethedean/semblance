# Publishing to PyPI

This repository publishes independently versioned packages:

| Package | `pyproject.toml` | Tag | PyPI |
|---|---|---|---|
| `semblance` | repo root | `v0.9.0` | https://pypi.org/project/semblance/ |
| `semblance-foundry` | `packages/semblance-foundry/` | `foundry-v0.1.3` | https://pypi.org/project/semblance-foundry/ |
| `semblance-databricks` | `packages/semblance-databricks/` | `databricks-v0.1.2` | https://pypi.org/project/semblance-databricks/ |

Tagging is the release. Pushing a matching tag runs [.github/workflows/release.yml](https://github.com/eddiethedean/semblance/blob/main/.github/workflows/release.yml): lint, typecheck, tests, security, then build and upload **only** the package that matches the tag. The workflow refuses to publish if the tag version does not equal the version in that package's `pyproject.toml`.

Do **not** tag `v0.1.0` for Foundry or Databricks — that pattern is reserved for core Semblance and would fail the version check.

## Prerequisites

1. **PyPI account** – [Register](https://pypi.org/account/register/) if needed.
2. **`semblance`** – API token stored as the `PYPI_API_TOKEN` GitHub secret (project-scoped to `semblance` is enough).
3. **`semblance-foundry` and `semblance-databricks`** – [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC). Publish jobs use `id-token: write` and must **not** set `username`/`password` (a project-scoped `PYPI_API_TOKEN` for `semblance` will 403 on adapter uploads).

Each adapter publisher must match this exactly:

| Field | Value |
|---|---|
| Owner | `eddiethedean` |
| Repository | `semblance` |
| Workflow filename | `release.yml` |
| Environment | *empty* (do not set a GitHub Environment on the job or on PyPI) |

For a project that does not exist yet, add a **pending** publisher with that project's name (`semblance-databricks`). The first successful `databricks-v*` tag creates the PyPI project.

## Release checklist

1. Working tree clean; CI green on `main`.
2. Version in the target `pyproject.toml` matches the intended tag.
3. Changelog section dated (not `Unreleased`) with compare/tag links.
4. Foundry README / docs still say unofficial / not affiliated with Palantir.
5. Databricks README / docs still say unofficial / not affiliated with Databricks.
6. Commit the version bump, push `main`, then tag:

```bash
# Core Semblance
git tag v0.9.0
git push origin v0.9.0

# Foundry adapter (separate tag, separate PyPI project)
git tag foundry-v0.1.3
git push origin foundry-v0.1.3

# Databricks adapter (separate tag, separate PyPI project)
git tag databricks-v0.1.2
git push origin databricks-v0.1.2
```

You cannot reuse a version number once it has been published.

## Manual build (optional)

From the project root, for Test PyPI or a local check:

```bash
pip install build twine
python -m build                          # semblance
python -m build packages/semblance-foundry
python -m build packages/semblance-databricks
twine check dist/* packages/semblance-foundry/dist/* packages/semblance-databricks/dist/*
```

Upload only if you are **not** using the GitHub release workflow for that version:

```bash
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_TOKEN twine upload dist/*
```

Test PyPI: `twine upload --repository testpypi dist/*`

## After publishing

- **Semblance:** `pip install semblance` — https://pypi.org/project/semblance/
- **Foundry:** `pip install semblance-foundry` — https://pypi.org/project/semblance-foundry/
- **Databricks:** `pip install semblance-databricks` — https://pypi.org/project/semblance-databricks/
- GitHub Releases are created from the same tag (core wheels on `v*`, Foundry wheels on `foundry-v*`, Databricks wheels on `databricks-v*`).
