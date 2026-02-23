# Roadmap

## Phase 1 — MVP (Foundations) ✓

- SemblanceAPI core
- GET endpoints
- Query parameter inputs
- Single & list outputs
- FromInput binding
- DateRangeFrom constraint
- Polyfactory integration
- FastAPI app export
- Basic pytest client

## Phase 2 — Practical Expansion ✓

- POST endpoints with body models
- Path parameter support (GET and POST)
- Pagination helpers (PageParams, PaginatedResponse)
- Deterministic seeding (SemblanceAPI(seed=), seed_from=)
- Error response simulation (error_rate, error_codes)
- Response count / limit constraints (list_count=, list_count="field")

## Phase 3 — Advanced Simulation ✓

- Conditional dependencies (WhenInput)
- Cross-field constraints (ComputedFrom)
- Collection filtering constraints (filter_by=)
- Nested model linking
- Optional stateful mode (SemblanceAPI(stateful=True))
- Latency & jitter simulation (latency_ms=, jitter_ms=)

## Phase 4 — Ecosystem & Polish ✓

- Plugin system for custom links
- OpenAPI schema annotations (summary, description, tags)
- CLI runner (`semblance run`, `semblance export`)
- Frontend mock export (OpenAPI + fixtures)
- Documentation site (MkDocs)
- Example galleries

## Phase 5 — Testing & Validation ✓

- **Property-based testing** — Hypothesis integration: `strategy_for_input_model()`, `test_endpoint()` in `semblance.property_testing`; generate inputs from input models, validate responses match output schema and optional invariants
- PUT, PATCH, DELETE endpoint support
- Optional response schema validation — `SemblanceAPI(validate_responses=True)` verifies generated responses conform to output model
- Rate limiting simulation — `rate_limit=N` requests per second per endpoint (sliding window, 429 when exceeded)

## Phase 6 — Stateful CRUD & Export ✓

- **Stateful PUT/PATCH/DELETE** ✓ — When `stateful=True`, PUT upsert by path + id, PATCH update by id, DELETE remove by id; extend `StatefulStore` with get-by-id, update, remove so list GET and single-item GET/PUT/PATCH/DELETE use stored data
- **Export and CLI** ✓ — Include PUT, PATCH, DELETE in `export fixtures` and OpenAPI example generation (minimal body/path params); `_sample_request` and schema iteration extended for put/patch/delete
- **OpenAPI polish** ✓ — Document 429 response when `rate_limit` is set; optional response descriptions for simulated error codes (4xx/5xx)

## Phase 7 — Developer Experience & Extensibility ✓

- **Built-in request links** ✓ — `FromHeader(name)`, `FromCookie(name)` for binding output fields to request headers/cookies (with `register_link`-style resolution)
- **Config file** ✓ — Optional defaults from `[tool.semblance]` in pyproject.toml or `semblance.yaml` (e.g. seed, validate_responses, stateful) via `SemblanceAPI(config_path=...)` or `SemblanceAPI.from_config()`
- **Pytest plugin** ✓ — Markers `@pytest.mark.semblance(app="module:attr")` and `@pytest.mark.semblance_property_tests(app="...")`; fixtures `semblance_api`, `semblance_client`; parametrized property tests per endpoint
- **Reproducible failures** ✓ — On Hypothesis failure in `test_endpoint`, error message includes "Reproduce with curl:" and "Or Python:" snippets
- **Mount and middleware** ✓ — `api.mount_into(parent_app, path_prefix)`; `api.add_middleware(MiddlewareClass, **kwargs)` applied in `as_fastapi()`

## Phase 8 — UX & Ergonomics (planned)

- **CLI onboarding**
  - `semblance init` — scaffold a minimal runnable app (+ optional `semblance.yaml`)
  - `semblance validate module:attr` — validate routes/links/config without starting a server (CI/pre-commit friendly)
  - `semblance run module` — infer `:api`/`:app` when unambiguous; improve `--help` with copy/paste examples
- **Faster-to-fix errors**
  - Validate link bindings at `as_fastapi()` (e.g. `FromInput("typo")`) with route/model/field in the error
  - Improve duplicate endpoint errors (include HTTP method + path + where possible)
  - Enrich stateful by-id errors (404 includes collection + id field/value, optionally behind a flag)
- **Docs that answer “why did this happen?”**
  - Troubleshooting / FAQ page (common 404/422/429/stateful/link issues)
  - Short “Concepts” overview (input/output models, links, seeding, stateful store, simulation options)
  - Cookbook/recipes page (pagination, stateful CRUD, request links, rate limiting, property tests)
