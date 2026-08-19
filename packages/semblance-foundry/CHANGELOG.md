# Changelog

All notable changes to `semblance-foundry` are documented in this file.

## [Unreleased]

## [0.1.2] - 2026-08-19

### Changed

- Depend on `semblance>=0.7.0,<0.9` so the adapter installs with Semblance 0.8.x. No new Foundry operations.

### Fixed

- Search page tokens include where/select so paging cannot cross filter scopes.
- `validate` applies the fixture (dangling links fail); `load_fixture` clears prior state and keeps query callbacks.
- CLI `--token` is required when `--auth strict`; `--host` is not overridden by env.

## [0.1.1] - 2026-08-19

### Fixed

- Page tokens reject HMAC length mismatch and stale revision after writes (400 `InvalidPageToken` instead of 500 or a silent offset).

## [0.1.0] - 2026-08-18

Ontology-read MVP. Independently versioned from `semblance` 0.7.0.

### Added

- Package `semblance-foundry` with `FoundryMock` / `FoundryMockConfig`
- Fixture v1 loader, bundled `acme` ontology, `load_bundled_fixture()`, deterministic RIDs
- Auth modes `disabled`, `optional` (default), `strict`
- Foundry-style error envelope and checksummed page tokens
- Ontology-read operations listed in `compatibility.yaml` (docs date 2026-08-18)
- CLI: `serve` (bundled acme if `--fixture` omitted), `validate`, `fixture init`, `operations`
- HTTP contract tests; optional `sdk` extra (`foundry-platform-sdk==1.101.0`) skipped unless installed

[Unreleased]: https://github.com/eddiethedean/semblance/compare/foundry-v0.1.2...HEAD
[0.1.2]: https://github.com/eddiethedean/semblance/compare/foundry-v0.1.1...foundry-v0.1.2
[0.1.1]: https://github.com/eddiethedean/semblance/compare/foundry-v0.1.0...foundry-v0.1.1
[0.1.0]: https://github.com/eddiethedean/semblance/releases/tag/foundry-v0.1.0
