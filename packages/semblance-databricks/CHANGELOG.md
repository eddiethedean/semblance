# Changelog

All notable changes to `semblance-databricks` are documented in this file.

## [Unreleased]

## [0.1.0] - 2026-08-19

Workspace compute / jobs / artifacts / permissions / SQL-statement MVP (Phase 10 A–D).

### Added

- Package `semblance-databricks` with `DatabricksMock` / `DatabricksMockConfig`
- Fixture v1 loader, bundled `acme` workspace, `load_bundled_fixture()`, deterministic IDs
- Auth modes `disabled`, `optional` (default), `strict`
- Databricks `{error_code, message}` errors and checksummed page tokens
- Virtual clock (`tick()`) for cluster and run lifecycle
- Operations listed in `compatibility.yaml` (docs date 2026-08-19)
- CLI: `serve` (port 8766; bundled acme if `--fixture` omitted), `validate`, `fixture init`, `operations`
- HTTP contract tests; optional `sdk` extra (`databricks-sdk==0.57.0`) skipped unless installed

### Fixed

- Job and run create IDs no longer overwrite bundled fixture `1001` / `2001`
- Jobs create persists top-level JobSettings (`tasks`, etc.)
- Cancel of terminal runs returns `INVALID_STATE`
- Page tokens reject HMAC length mismatch and stale revision after writes
- Invalid JSON bodies return 400 instead of empty-object creates
- DBFS put stores base64 contents and refuses path traversal in the temp-dir backend

[Unreleased]: https://github.com/eddiethedean/semblance/compare/databricks-v0.1.0...HEAD
[0.1.0]: https://github.com/eddiethedean/semblance/releases/tag/databricks-v0.1.0
