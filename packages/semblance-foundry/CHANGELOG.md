# Changelog

All notable changes to `semblance-foundry` are documented in this file.

## [Unreleased]

## [0.1.0] - 2026-08-18

Ontology-read MVP. Independently versioned from `semblance` 0.7.0.

[Unreleased]: https://github.com/eddiethedean/semblance/compare/foundry-v0.1.0...HEAD
[0.1.0]: https://github.com/eddiethedean/semblance/releases/tag/foundry-v0.1.0

### Added

- Package `semblance-foundry` with `FoundryMock` / `FoundryMockConfig`
- Fixture v1 loader, bundled `acme` ontology, `load_bundled_fixture()`, deterministic RIDs
- Auth modes `disabled`, `optional` (default), `strict`
- Foundry-style error envelope and checksummed page tokens
- Ontology-read operations listed in `compatibility.yaml` (docs date 2026-08-18)
- CLI: `serve` (bundled acme if `--fixture` omitted), `validate`, `fixture init`, `operations`
- HTTP contract tests; optional `sdk` extra (`foundry-platform-sdk==1.101.0`) skipped unless installed
