# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2025-02-23

### Added

#### Phase 8 — UX & Ergonomics
- **CLI onboarding** — `semblance init` scaffolds a minimal runnable app (optional `semblance.yaml`); `semblance validate module:attr` validates routes, links, and config without starting a server (CI/pre-commit friendly); `semblance run module` infers `:api`/`:app` when unambiguous, with improved `--help` and copy/paste examples.
- **Faster-to-fix errors** — Link bindings validated at `as_fastapi()` (e.g. invalid `FromInput("typo")`) with route/model/field in the error; duplicate endpoint errors include HTTP method and path; stateful 404s can include collection and id (behind `verbose_errors` flag).
- **Docs** — Troubleshooting/FAQ (common 404/422/429, stateful, link issues); Concepts overview (input/output models, links, seeding, stateful store, simulation options); Cookbook/recipes (pagination, stateful CRUD, request links, rate limiting, property tests).

## [0.5.0] - 2025-02-23

### Added

#### Phase 6 — Stateful CRUD & Export
- **Stateful GET by id** — For routes like `/users/{id}`, returns the stored item when `stateful=True`, or 404 if not found.
- **Stateful PUT** — Upsert by path + id: replaces existing or adds new; returns the upserted instance.
- **Stateful PATCH** — Update by id; returns 404 if the item is not in the store.
- **Stateful DELETE** — Removes item by id; returns 204 when found, 404 when not.
- **Export and CLI** — `export fixtures` and OpenAPI example generation include PUT, PATCH, DELETE (path params and minimal body).
- **OpenAPI** — 429 response documented when `rate_limit` is set; optional response descriptions for simulated error codes.

#### Phase 7 — Developer Experience & Extensibility
- **Request links** — `FromHeader(name)` and `FromCookie(name)` to bind output fields to request headers and cookies.
- **Config file** — Optional defaults from `semblance.yaml` or `[tool.semblance]` in pyproject.toml via `SemblanceAPI(config_path=...)` or `SemblanceAPI.from_config()` (seed, validate_responses, stateful).
- **Pytest plugin** — Markers `@pytest.mark.semblance(app="module:attr")` and `@pytest.mark.semblance_property_tests(app="...")`; fixtures `semblance_api`, `semblance_client`; parametrized property tests per endpoint.
- **Reproducible failures** — On Hypothesis failure in `test_endpoint`, error message includes "Reproduce with curl:" and "Or Python:" snippets.
- **Mount and middleware** — `api.mount_into(parent_app, path_prefix)`; `api.add_middleware(MiddlewareClass, **kwargs)` in `as_fastapi()`.

#### Documentation and examples
- **Guides** — Request Links guide (`guides/request-links.md`) for FromHeader and FromCookie.
- **Examples** — Phase 5: `put_patch_delete` (PUT/PATCH/DELETE); Phase 6: `stateful_crud` (full CRUD); Phase 7: `request_links` (headers and cookies). All wired in `run_examples.py` and docs nav.

### Fixed

- **TestClient** — `test_from_cookie_binding` now sets cookies on the client instance instead of per-request, resolving Starlette/httpx deprecation warning.

## [0.4.0] - 2025-02-23

### Changed

- **Typing** — Stricter type annotations: `api.py` stateful PUT/PATCH narrow `response` to `BaseModel`; `property_testing` uses `_HTTPClientProtocol`/`_ResponseProtocol`; `plugins` `LinkProtocol.resolve` and `register_link` typed; `export` uses `JSONResponse` alias. Mypy: `warn_unused_ignores`, `no_implicit_optional`, and `strict_optional` overrides per module; removed unused `type: ignore` in `cli.py`. Test fixtures: explicit `SemblanceAPI` return types where applicable.
- **Tests** — `test_post_with_seed_from_input` made deterministic by supplying date range in POST body so `DateRangeFrom` override is used.
- **Lint** — Unused imports removed and import order fixed in tests (ruff).

## [0.3.0] - 2025-02-23

### Added

#### Phase 5 — Testing & Validation
- **PUT, PATCH, DELETE** — `@api.put()`, `@api.patch()`, `@api.delete()`; DELETE with `output=None` returns 204 No Content, or 200 with generated body
- **Rate limiting** — `rate_limit=N` per endpoint (sliding 1s window); returns 429 when exceeded (`src/semblance/rate_limit.py`)
- **Response validation** — `SemblanceAPI(validate_responses=True)` validates generated responses against the output model (dev/CI)
- **Property-based testing** — `semblance.property_testing`: `strategy_for_input_model()`, `test_endpoint()` with Hypothesis (optional dep in `[dev]`)
- Phase 5 tests in `tests/test_phase5.py`

### Changed
- **Typing** — `disallow_untyped_defs = true` for `semblance.*`; annotations added in `cli.py`, `export.py`, `conftest.py`; mypy fixes for api/factory/property_testing
- **Docs** — README, roadmap, guides (simulation-options, testing, input-output-binding, api), and planning doc updated for Phase 5 and new options

## [0.2.2] - 2025-02-13

### Fixed

- `filter_by` now applied when using `PaginatedResponse[Model]` (was ignored previously)

### Added

- Phase 5 to roadmap: property-based testing, PUT/PATCH/DELETE, response validation, rate limiting

### Changed

- README: feature matrix replacing competitors table, Read the Docs links, emoji icons with hover tooltips

## [0.2.1] - 2025-02-13

### Added

- Example docs: full Semblance code in each example page with reproducible outputs
- run_examples.py: doc_basic, doc_pagination, doc_nested, doc_stateful, doc_advanced, doc_error_simulation, doc_plugins

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

[Unreleased]: https://github.com/eddiethedean/semblance/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.6.0
[0.5.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.5.0
[0.4.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.4.0
[0.3.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.3.0
[0.2.2]: https://github.com/eddiethedean/semblance/releases/tag/v0.2.2
[0.2.1]: https://github.com/eddiethedean/semblance/releases/tag/v0.2.1
[0.2.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.2.0
[0.1.0]: https://github.com/eddiethedean/semblance/releases/tag/v0.1.0
