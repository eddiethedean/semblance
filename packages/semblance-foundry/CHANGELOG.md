# Changelog

All notable changes to `semblance-foundry` are documented in this file.

## [0.1.0] - Unreleased

Ontology-read MVP. Not tagged or published yet.

### Added

- Package `semblance-foundry` with `FoundryMock` / `FoundryMockConfig`
- Fixture v1 loader, bundled `acme` ontology, deterministic RIDs
- Auth modes `disabled`, `optional` (default), `strict`
- Foundry-style error envelope and checksummed page tokens
- Ontology-read operations listed in `compatibility.yaml` (docs date 2026-08-18)
- CLI: `serve`, `validate`, `fixture init`, `operations`
- HTTP contract tests; optional `sdk` extra (`foundry-platform-sdk==1.101.0`) skipped unless installed
