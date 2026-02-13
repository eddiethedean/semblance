# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2025-02-13

### Fixed

- CLI `--reload` now resolves SemblanceAPI via `as_fastapi()` so `app:api` works with reload
- CLI guards against `spec.loader` being None (e.g. namespace packages)

## [0.2.0] - 2025-02-13

### Added

- GitHub Actions CI (test matrix, ruff, mypy, bandit, pip-audit)
- Release workflow with PyPI publish on version tags
- Pre-commit hooks (ruff, pre-commit-hooks)
- CONTRIBUTING.md, SECURITY.md, LICENSE.md
- Bandit and pip-audit in dev dependencies
- CLI guide and Plugins guide
- Error-simulation and plugins example galleries with runnable scripts

### Changed

- README: Ruff badge, GitHub links, CONTRIBUTING reference
- Development Status: Alpha to Beta
- Package metadata: authors, license, project URLs

## [0.1.0] - 2025-02-13

### Added

#### Phase 1 — MVP
- SemblanceAPI core with GET endpoints
- Query parameter inputs and single/list outputs
- FromInput binding and DateRangeFrom constraint
- Polyfactory integration for response generation
- FastAPI app export and basic test client

#### Phase 2 — Practical Expansion
- POST endpoints with body models
- Path parameter support (GET and POST)
- Pagination helpers (PageParams, PaginatedResponse)
- Deterministic seeding (`SemblanceAPI(seed=)`, `seed_from=`)
- Error response simulation (`error_rate`, `error_codes`)
- Response count constraints (`list_count=`, `list_count="field"`)

#### Phase 3 — Advanced Simulation
- Conditional dependencies (WhenInput)
- Cross-field constraints (ComputedFrom)
- Collection filtering constraints (`filter_by=`)
- Nested model linking
- Optional stateful mode (`SemblanceAPI(stateful=True)`)
- Latency and jitter simulation (`latency_ms=`, `jitter_ms=`)

#### Phase 4 — Ecosystem & Polish
- Plugin system for custom links
- OpenAPI schema annotations (summary, description, tags)
- CLI runner (`semblance run`, `semblance export`)
- Frontend mock export (OpenAPI schema + JSON fixtures)
- Documentation site (MkDocs)
- Example galleries

[Unreleased]: https://github.com/eddiethedean/semblance/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/eddiethedean/semblance/releases/tag/v0.2.1
[0.2.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.2.0
[0.1.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.1.0
