# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Package | Version | Supported |
|---|---|---|
| semblance | 0.9.x | :white_check_mark: |
| semblance | 0.8.x | :white_check_mark: |
| semblance | 0.7.x | :white_check_mark: |
| semblance | 0.6.x | :white_check_mark: |
| semblance | < 0.6 | :x: |
| semblance-foundry | 0.1.x | :white_check_mark: |
| semblance-databricks | 0.1.x | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Email the maintainers or open a [private security advisory](https://github.com/eddiethedean/semblance/security/advisories/new) on GitHub.
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to acknowledge reports within 48 hours and will work with you to understand and address the issue.

## Security Considerations

- **Semblance is for mock/simulation** — Use it for prototyping, testing, and development. Do not use it as a production API backend without additional hardening.
- **Foundry adapter** — `semblance-foundry` is an unofficial test double. Do not put production secrets in fixtures or mock tokens. Authentication errors never echo tokens.
- **Databricks adapter** — `semblance-databricks` is an unofficial test double. Secret REST is metadata only; never put production tokens in fixtures. Authentication errors never echo tokens.
- **Dependencies** — We rely on FastAPI, Pydantic, Polyfactory, and Uvicorn. Keep these and your Python environment updated: `pip install -U pip semblance`.
- **Randomness** — Semblance uses `random` for test data generation and latency simulation, not for cryptographic purposes.

## Security Checks

For local auditing:

```bash
pip install bandit pip-audit
bandit -r src/ packages/semblance-foundry/src packages/semblance-databricks/src -ll
pip-audit
```
