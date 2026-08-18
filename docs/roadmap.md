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

## Phase 8 — UX & Ergonomics ✓

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

## Phase 9 — External API Mock Packages: Foundry ✓

Ontology-read MVP for an unofficial `semblance-foundry` adapter. Detailed spec: [Semblance Foundry Package Plan](semblance_foundry_plan.md). Workspace `pythonpath` / ruff / mypy plumbing lives in [Phase 11](#phase-11--core-infrastructure-for-multi-package-development); Foundry tests plug into those paths rather than duplicating CI matrix work here.

- **Package bootstrap** ✓ — `packages/semblance-foundry/` with `pyproject.toml`, `semblance_foundry` import, `FoundryMock` / `FoundryMockConfig`, CLI (`serve`, `validate`, `fixture init`, `operations`), tests layout, unofficial/non-affiliation notice. Independently versioned; depends on `semblance` via a normal version range.
- **Compatibility model** ✓ — per-operation `compatibility.yaml` with support levels `exact` | `representative` | `stub` | `unsupported`, docs URL + verification date (public API v2, dated 2026-08-18 unless a newer pass is recorded), and tests that prove the level; expose `/.well-known/foundry-mock-compatibility.json`. Unknown paths return 404; known-but-unimplemented operations may return 501 only in `strict` mode.
- **Fixture-backed ontology graph** ✓ — YAML/JSON fixture v1: one ontology, two object types, links, one action type (metadata only), one query type; deterministic RIDs; load-time validation (duplicate API names / primary keys). Process-local state only; no restart durability.
- **Ontology read operations (MVP)** ✓ — public API v2:
  - `GET /api/v2/ontologies`
  - `GET /api/v2/ontologies/{ontology}`
  - `GET /api/v2/ontologies/{ontology}/objectTypes`
  - `GET /api/v2/ontologies/{ontology}/objectTypes/{objectType}`
  - `GET /api/v2/ontologies/{ontology}/objects/{objectType}`
  - `GET /api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}`
  - `POST /api/v2/ontologies/{ontology}/objects/{objectType}/search` (representative: eq/and filters only)
  - `GET /api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/links/{linkType}`
  - `GET /api/v2/ontologies/{ontology}/actionTypes` and get-by-name (metadata; no apply)
  - `GET /api/v2/ontologies/{ontology}/queryTypes` and get-by-name
  - `POST /api/v2/ontologies/{ontology}/queries/{queryApiName}/execute` (static fixture or allow-listed Python callback; never eval fixture expressions)
- **Auth, errors, pagination** ✓ — auth modes `disabled`, `optional` (default), and `strict`; Foundry-style error envelope; opaque checksummed page tokens owned by the adapter (`PageTokenCodec`); request-id header. Do not add Foundry-shaped helpers to core unless a second adapter immediately needs the same primitive.
- **Testing surface** ✓ — `FoundryMock.as_fastapi()`, pytest context/fixtures, golden HTTP contracts. HTTP contract tests are required; one pinned `foundry-platform-sdk` version is the compatibility acceptance test (optional/non-blocking if the SDK cannot target localhost in CI). No live Foundry; no network in unit/contract tests.
- **Exit criterion** ✓ — HTTP client (and SDK if CI-feasible) lists fixture objects across two pages, gets by primary key, follows one link, and executes one configured query — all locally.

### Later (see Foundry plan)

Not Phase 9: apply/applyBatch actions, aggregates, object sets, datasets/transactions, orchestration/streams, Foundry 1.0. Those are post–Phase 9 milestones in the [Foundry plan](semblance_foundry_plan.md).

## Phase 10 — External API Mock Packages: Databricks

- **`semblance-databricks` package bootstrap and workspace integration**
  - Add package scaffold under `packages/semblance-databricks/`
  - Add adapter-specific `pyproject.toml`, typed API surface, CLI entrypoint, and test entry points
  - Add compatibility manifest support and API operation registry for Databricks endpoints
- **Phase A — Workspace and identity foundation**
  - Implement `clusters` and `jobs` list/get, `jobs/runs/get`, basic workspace status endpoints
  - Add auth modes, deterministic IDs, cursor pagination, and unknown endpoint semantics
  - Add cluster startup lifecycle simulation with deterministic states (`PENDING`, `RUNNING`, `ERROR`, `TERMINATING`)
- **Phase B — Stateful compute and runs**
  - Add cluster/job creation/edit/restart/terminate/delete flows
  - Add run submit/cancel/get-status with deterministic state transitions
  - Add SQL warehouse basic CRUD and secrets read/list/put scaffolding
- **Phase C — Compute artifacts and storage**
  - Add run output/runs logs, cluster events, lightweight DBFS-like file stubs
  - Add temporary-file and in-memory storage backend controls
- **Phase D — Advanced APIs (incremental)**
  - Add permissions and SQL statement simulation with paginated results
  - Add audit/event listing and explicit unsupported-endpoint handling
- **Deliverables**
  - README/fixtures schema docs and non-affiliation notice
  - CLI commands: `serve`, `validate`, `fixture init`, `operations`
  - CI coverage with contract/golden tests and optional official client compatibility checks

## Phase 11 — Core Infrastructure for Multi-Package Development

- **Shared test/lint/type-check surface in core tool config**
  - include package source trees in lint/type-check path config
  - document pytest commands that include package test trees when available
  - allow stable imports from `src/`, `packages/semblance-foundry/src`, `packages/semblance-databricks/src`
- **Developer onboarding docs for multi-package installs**
  - contribution docs with editable installs for each package
  - README development commands that install all active packages
- **Monorepo CI shape**
  - single command matrix for core + both packages
  - independent package test slices to keep failures actionable
  - workspace-wide checks that preserve per-package dependency boundaries
- **Cross-package dependency hygiene**
  - pin shared dev tooling in root
  - keep package-specific extras isolated unless intentionally shared
- **Deliverable**
  - Seamless local development from one environment where both adapter packages can be built and tested without path hacks
