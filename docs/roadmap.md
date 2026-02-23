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

## Phase 7 — Developer Experience & Extensibility

- **Built-in request links** — `FromHeader(name)`, `FromCookie(name)` for binding output fields to request headers/cookies (with `register_link`-style resolution)
- **Config file** — Optional defaults from `[tool.semblance]` in pyproject.toml or `semblance.yaml` (e.g. default seed, list_count, validate_responses) when using CLI or programmatic build
- **Pytest plugin** — Auto-discover Semblance apps (or accept marker) and generate Hypothesis-based property tests per endpoint; optional `@semblance.parametrize` or fixture for app + client
- **Reproducible failures** — On Hypothesis failure in property tests, print minimal reproduction (curl command or short Python snippet) for debugging
- **Mount and middleware** — Mount a SemblanceAPI at a path prefix on an existing FastAPI app; allow registering custom FastAPI middleware before/after Semblance routes
