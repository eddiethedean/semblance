# Publishing to PyPI

## Prerequisites

1. **PyPI account** – [Register](https://pypi.org/account/register/) if needed.
2. **API token (recommended)** – PyPI → Account settings → API tokens. Create a token with scope “Entire account” or “Project: semblance”.

## Build

From the project root:

```bash
pip install build
python -m build
```

Artifacts are created in `dist/`.

## Publish

### Option A: API token (recommended)

```bash
pip install twine
twine upload dist/*
```

When prompted:
- **Username:** `__token__`
- **Password:** your PyPI API token (starts with `pypi-`)

Or non-interactive:

```bash
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-YOUR_TOKEN twine upload dist/*
```

### Option B: Test PyPI first

To try the upload to Test PyPI without publishing to the real index:

```bash
twine upload --repository testpypi dist/*
```

Install from Test PyPI: `pip install -i https://test.pypi.org/simple/ semblance`

### Option C: Trusted publishing (no token in env)

On GitHub Actions you can use [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) so no token is stored in the repo.

## After publishing

- **PyPI project:** https://pypi.org/project/semblance/
- **Install:** `pip install semblance`

## Version bumps

Before each release, update `version` in `pyproject.toml`, then rebuild and upload. You cannot reuse a version number once it has been published.
