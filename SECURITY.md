# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

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
- **Dependencies** — We rely on FastAPI, Pydantic, Polyfactory, and Uvicorn. Keep these and your Python environment updated: `pip install -U pip semblance`.
- **Randomness** — Semblance uses `random` for test data generation and latency simulation, not for cryptographic purposes.

## Security Checks

For local auditing:

```bash
pip install bandit pip-audit
bandit -r src/
pip-audit
```
