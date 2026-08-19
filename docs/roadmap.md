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

## Phase 10 — External API Mock Packages: Databricks ✓

Unofficial `semblance-databricks` adapter covering workspace compute, jobs, artifacts, permissions, and SQL statements (phases A–D). Detailed spec: [Semblance Databricks Package Plan](semblance_databricks_plan.md). Workspace `pythonpath` / ruff / mypy plumbing lives in [Phase 11](#phase-11--core-infrastructure-for-multi-package-development); Databricks tests plug into those paths rather than duplicating CI matrix work here. `DatabricksMock` is a custom FastAPI factory (same reason as Foundry: core ignores handler bodies). Independently versioned; depends on `semblance>=0.7.0,<0.9`. Public REST pinned **2026-08-19** (Jobs **2.2**, Clusters **2.1**, SQL/DBFS/secrets/permissions **2.0**).

- **Package bootstrap** ✓ — `packages/semblance-databricks/` with `pyproject.toml`, `semblance_databricks` import, `DatabricksMock` / `DatabricksMockConfig`, CLI (`serve` default port 8766, `validate`, `fixture init`, `operations`), tests layout, unofficial/non-affiliation notice.
- **Compatibility model** ✓ — per-operation `compatibility.yaml` with support levels `exact` | `representative` | `stub` | `unsupported`, docs URL + verification date, and tests that prove the level; expose `/.well-known/semblance-databricks-compat.json`. Unknown paths return 404; known-but-unimplemented operations may return 501 only in `strict` mode. Optional Jobs 2.1 aliases are `representative`, not primary.
- **Fixture-backed workspace** ✓ — YAML/JSON fixture v1: bundled `acme` with clusters spanning two list pages, ≥2 jobs, ≥1 run, warehouse, secret-scope **metadata** (no secret values on REST), DBFS stubs, one workspace path. Deterministic IDs; load-time validation. Process-local state; capped temp-dir opt-in for DBFS only.
- **Phase A — reads** ✓ — public REST:
  - `GET /api/2.1/clusters/list` and `GET /api/2.1/clusters/get`
  - `GET /api/2.2/jobs/list`, `GET /api/2.2/jobs/get`, `GET /api/2.2/jobs/runs/get`
  - `GET /api/2.0/workspace/get-status` (object **path**, not workspace health)
  - `GET /api/2.0/preview/scim/v2/Me` if the pinned SDK requires current user
- **Phase B — writes and lifecycle** ✓ — cluster create/edit/delete/restart; jobs create/reset/delete; runs submit/cancel; SQL warehouses `/api/2.0/sql/warehouses`; workspace secrets `GET/POST /api/2.0/secrets/...` (keys only). Virtual-clock cluster/run states (`PENDING` → `RUNNING` / `ERROR`, cancel → `TERMINATED`).
- **Phase C — artifacts** ✓ — libraries install/uninstall, `GET /api/2.2/jobs/runs/get-output`, cluster events, DBFS `list`/`read` and `POST /api/2.0/dbfs/add-block` stub. No invented audit-log URLs.
- **Phase D — permissions and SQL** ✓ — `GET`/`PATCH /api/2.0/permissions/{object_type}/{object_id}`; `POST`/`GET /api/2.0/sql/statements` (fixture or allow-listed callback chunks; no Spark SQL).
- **Auth, errors, pagination** ✓ — auth modes `disabled`, `optional` (default), and `strict`; Databricks `{error_code, message}` (not Foundry envelopes); opaque checksummed page tokens owned by the adapter (`PageTokenCodec` copy); request-id header. Do not add Databricks-shaped helpers to core in Phase 10.
- **Testing surface** ✓ — `DatabricksMock.as_fastapi()`, pytest context/fixtures, golden HTTP contracts. HTTP contract tests are required; one pinned `databricks-sdk` version is the compatibility acceptance test (optional/non-blocking if the SDK cannot target localhost in CI). No live Databricks; no network in unit/contract tests.
- **Exit criterion** ✓ — HTTP client (and SDK if CI-feasible) lists fixture clusters across two pages, gets a cluster and job, gets a run, drives one virtual-clock write (create/restart cluster or submit/cancel run), lists secret keys without values, and hits get-status plus one SQL statement or permissions get — all locally.

### Later (see Databricks plan)

Not Phase 10: Unity Catalog (including UC secrets), Model Serving, Spark Declarative Pipelines / DLT, Jobs 2.0 as primary, OAuth, Databricks adapter 1.0. Those are post–Phase 10 in the [Databricks plan](semblance_databricks_plan.md).

## Phase 11 — Core Infrastructure for Multi-Package Development ✓

Workspace plumbing so core + both adapters develop from one environment without path hacks. Do not extract `PageTokenCodec` (or other vendor-shaped helpers) into core in this phase; Foundry and Databricks copies wrap different error types. Leave extraction for a later phase if the codecs stay identical.

### Already in tree

- Root `pyproject.toml` pytest `pythonpath`, ruff `src`, and mypy `mypy_path` include `src/`, `packages/semblance-foundry/src`, and `packages/semblance-databricks/src`.
- CONTRIBUTING and README document editable installs for core + both adapters.
- Workspace lint, mypy, and security jobs cover all three packages.

### Remaining work (done)

- **CI slices** ✓ — Pytest matrix `package: [core, foundry, databricks]` on the same OS/Python matrix, `-m "not sdk"`. Lint/mypy/security stay workspace-wide. Each slice reports coverage for that tree.
- **Install/cache hygiene** ✓ — Pip cache keys hash all three `pyproject.toml` files. README Development and CONTRIBUTING use the three pytest slices.
- **Dependency boundaries** ✓ — `tests/test_package_boundaries.py`: adapters do not import each other or `semblance._*`. Root `dev` extra pins `ruff==0.16.3`; adapter `[dev]` extras remain for package-only installs.
- **Tree hygiene** ✓ — Unpack glob ignored; ruff excludes `semblance_*-*` leftover sdist dirs.
- **Docs** ✓ — CONTRIBUTING clean-clone block; [publishing](publishing.md) example tags `v0.8.0` / `foundry-v0.1.2` / `databricks-v0.1.1`.

### Release versions

| Package | From | To | Tag |
|---|---|---|---|
| `semblance` | 0.7.0 | **0.8.0** | `v0.8.0` |
| `semblance-foundry` | 0.1.1 | **0.1.2** | `foundry-v0.1.2` |
| `semblance-databricks` | 0.1.0 | **0.1.1** | `databricks-v0.1.1` |

Adapters depend on **`semblance>=0.7.0,<0.9`**. Publish order: **core `v0.8.0` first**, then adapter tags (tagging is a separate step; see [publishing](publishing.md)).

### Acceptance

- From one venv: editable installs of all three packages; both adapters build and test without path hacks.
- CI uses independent test slices.
- Versions and changelogs dated for 0.8.0 / 0.1.2 / 0.1.1.

## Phase 12 — Declarative Simulation APIs

Core APIs so downstream simulators stop dropping to Starlette middleware and one-off handlers. The ten open [`enhancement` issues](https://github.com/eddiethedean/semblance/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) are the backlog; this phase ships the **core-library slice** plus adapter dependency-range bumps. Issues were written against consumer simulators (`tests/simulators/…`) that are **not** in this repo — implement against `SemblanceAPI` / link plugins, do not import those files.

Do **not** extract `PageTokenCodec` (or other vendor-shaped helpers) into core. Do **not** replace Foundry/Databricks auth modes or error envelopes. Adapters keep custom FastAPI factories (handlers are still ignored by core). Native bytes/streaming ([#2](https://github.com/eddiethedean/semblance/issues/2)) waits until an in-tree adapter needs `/content` or `/upload`.

Prefer backward-compatible defaults; new strictness is opt-in.

### Already in tree

- Pydantic input models already validate query, path, and body ([#6](https://github.com/eddiethedean/semblance/issues/6) is mostly this).
- `WhenInput` for conditional field links; `FromHeader` / `FromCookie` for request binding.
- `PageParams` / `PaginatedResponse` for offset/limit lists; adapters own opaque page tokens.
- Route `error_rate` / `error_codes`; `stateful=True` + `StatefulStore` for CRUD-shaped mutation.
- Adapter Bearer (`disabled` / `optional` / `strict`) and vendor error JSON — not core route auth.

`FromJsonFixture` / `FromNestedFixture` named in the issues **do not exist** in semblance; Phase 12 adds fixture links rather than tightening types that are already shipped.

### Remaining work

- **Route Bearer ([#1](https://github.com/eddiethedean/semblance/issues/1))** — Declare Bearer on the route (tokens + 401 when missing/invalid). Default stays open. Do not echo tokens. Adapters do not switch to this helper in this phase.
- **Error maps ([#7](https://github.com/eddiethedean/semblance/issues/7), [#8](https://github.com/eddiethedean/semblance/issues/8))** — Declarative status + body (or fixture) keyed by input predicate (invalid combo, unsupported, unauthorized). Complements `error_rate`; does not replace adapter envelopes.
- **Fixture links ([#3](https://github.com/eddiethedean/semblance/issues/3), [#4](https://github.com/eddiethedean/semblance/issues/4), [#5](https://github.com/eddiethedean/semblance/issues/5))** — JSON fixture links with input-aware variant selection, list index/filter selectors, and per-link `strict` miss (raise instead of silent empty). Default miss behavior stays non-strict.
- **Pagination fixtures ([#9](https://github.com/eddiethedean/semblance/issues/9))** — First-class page sequence / page map on top of existing pagination helpers. Do not fold adapter `PageTokenCodec` into core.
- **Scenario steps ([#10](https://github.com/eddiethedean/semblance/issues/10))** — Lightweight per-route response sequence (e.g. 503 then 200, token-expiry then success). Not a workflow engine; `StatefulStore` remains the CRUD store.
- **Validation docs ([#6](https://github.com/eddiethedean/semblance/issues/6))** — Cookbook for required params, enums, and pattern constraints via Pydantic `Field`. Add a core helper only if a gap remains after docs.
- **Adapter ranges** — Widen `semblance-foundry` / `semblance-databricks` to include 0.9.x; no new Foundry/Databricks operations in this phase.

### Not this phase

- [#2](https://github.com/eddiethedean/semblance/issues/2) binary/streaming bodies and content-type overrides.
- Foundry apply/datasets/content, Databricks Unity Catalog / serving (still post–Phase 9 / 10).
- Migrating adapter routers onto core Bearer, error maps, or fixture links.
- Extracting `PageTokenCodec` into core.

### Issue routing

| Issue | Owner | Phase 12 |
|---|---|---|
| [#1](https://github.com/eddiethedean/semblance/issues/1) Bearer routes | core | yes |
| [#2](https://github.com/eddiethedean/semblance/issues/2) binary bodies | core | later |
| [#3](https://github.com/eddiethedean/semblance/issues/3) conditional fixtures | core | yes (new links) |
| [#4](https://github.com/eddiethedean/semblance/issues/4) fixture-miss strict | core | yes |
| [#5](https://github.com/eddiethedean/semblance/issues/5) collection selectors | core | yes |
| [#6](https://github.com/eddiethedean/semblance/issues/6) param validation | core | docs first |
| [#7](https://github.com/eddiethedean/semblance/issues/7) status/body errors | core | yes |
| [#8](https://github.com/eddiethedean/semblance/issues/8) invalid-input errors | core | yes (with #7) |
| [#9](https://github.com/eddiethedean/semblance/issues/9) pagination fixtures | core | yes |
| [#10](https://github.com/eddiethedean/semblance/issues/10) scenario steps | core | yes (lightweight) |

Mark a row done only when code, tests, and user-facing docs for that issue are in tree. Close the GitHub issue in the same change.

### Release versions

| Package | From | To | Tag |
|---|---|---|---|
| `semblance` | 0.8.0 | **0.9.0** | `v0.9.0` |
| `semblance-foundry` | 0.1.2 | **0.1.3** | `foundry-v0.1.3` |
| `semblance-databricks` | 0.1.1 | **0.1.2** | `databricks-v0.1.2` |

Adapters depend on **`semblance>=0.8.0,<1.0`** so 0.9.x installs (today’s `<0.9` would block it). Publish order: **core `v0.9.0` first**, then adapter tags ([publishing](publishing.md)).

### Acceptance

- In-scope issues (#1, #3–#10) implemented or documented as specified; #2 still open and pointed at a later phase.
- Defaults unchanged for existing apps; strict fixture-miss and Bearer are opt-in.
- Adapters still build against core without using the new helpers internally.
- CI slices stay green; changelogs dated for 0.9.0 / 0.1.3 / 0.1.2.
