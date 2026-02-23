# Contributing to Semblance

Thanks for your interest in contributing to Semblance. This document covers how to set up a development environment and submit contributions.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/eddiethedean/semblance.git
   cd semblance
   ```

2. **Create a virtual environment and install in editable mode**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Optional: Install pre-commit hooks**
   ```bash
   pre-commit install
   ```
   This runs ruff and other checks before each commit.

## Running Checks

Before submitting a pull request, ensure the following pass:

- **Tests**
  ```bash
  pytest tests/ -v --cov=src/semblance --cov-fail-under=85
  ```
  Run from the project root so that `examples.*` imports work (e.g. in `test_doc_examples`). If you add a new entry to `docs/guides/examples/run_examples.py` (the `EXAMPLES` list), the callable must return successfully; `test_run_examples_produces_valid_output` enforces that.

- **Lint (ruff)**
  ```bash
  ruff check src tests
  ruff format --check src tests
  ```

- **Type check (mypy)**
  ```bash
  mypy src
  ```

- **Security (bandit, pip-audit)**
  ```bash
  bandit -r src/ -ll
  pip-audit
  ```

## Building documentation

Documentation is built with MkDocs and hosted on [Read the Docs](https://semblance.readthedocs.io/). To build locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Open http://127.0.0.1:8000 to preview. Read the Docs builds from `.readthedocs.yaml` on each push.

## Submitting Changes

1. Create a branch from `main` for your changes
2. Make your changes with clear, focused commits
3. Ensure all checks pass locally
4. Open a pull request against `main`
5. Include a description of the change and any related issues

## Reporting Security Vulnerabilities

Please do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for how to report them responsibly.

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Run `ruff check src tests` to verify style compliance.
