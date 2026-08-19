# Publishing to PyPI

This repository publishes independently versioned packages:

| Package | `pyproject.toml` | Tag | PyPI |
|---|---|---|---|
| `semblance` | repo root | `v0.7.0` | https://pypi.org/project/semblance/ |
| `semblance-foundry` | `packages/semblance-foundry/` | `foundry-v0.1.1` | https://pypi.org/project/semblance-foundry/ |
| `semblance-databricks` | `packages/semblance-databricks/` | `databricks-v0.1.0` | not published yet |

Tagging is the release. Pushing a matching tag runs [.github/workflows/release.yml](https://github.com/eddiethedean/semblance/blob/main/.github/workflows/release.yml): lint, typecheck, tests, security, then build and upload **only** the package that matches the tag. The workflow refuses to publish if the tag version does not equal the version in that package's `pyproject.toml`.

Do **not** tag `v0.1.0` for Foundry or Databricks — that pattern is reserved for core Semblance and would fail the version check. Do not push adapter tags until a publish pass.

## Prerequisites

1. **PyPI account** – [Register](https://pypi.org/account/register/) if needed.
2. **`semblance`** – API token stored as the `PYPI_API_TOKEN` GitHub secret (project-scoped to `semblance` is enough).
3. **`semblance-foundry`** – [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) on PyPI for this repo, workflow `release.yml`, no GitHub Environment. The Foundry publish job uses OIDC (`id-token: write`) and does not use `PYPI_API_TOKEN`.
4. **`semblance-databricks`** – same Trusted Publishing / OIDC pattern as Foundry (`databricks-v*` tags). Register the publisher on PyPI before the first Databricks tag.

## Release checklist

1. Working tree clean; CI green on `main`.
2. Version in the target `pyproject.toml` matches the intended tag.
3. Changelog section dated (not `Unreleased`) with compare/tag links.
4. Foundry README / docs still say unofficial / not affiliated with Palantir.
5. Databricks README / docs still say unofficial / not affiliated with Databricks.
6. Commit the version bump, push `main`, then tag:

```bash
# Core Semblance
git tag v0.7.0
git push origin v0.7.0

# Foundry adapter (separate tag, separate PyPI project)
git tag foundry-v0.1.1
git push origin foundry-v0.1.1

# Databricks adapter (do not push until a publish pass)
# git tag databricks-v0.1.0
# git push origin databricks-v0.1.0
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
- **Databricks:** `pip install semblance-databricks` — after `databricks-v*` is tagged
- GitHub Releases are created from the same tag (core wheels on `v*`, Foundry wheels on `foundry-v*`, Databricks wheels on `databricks-v*`).
