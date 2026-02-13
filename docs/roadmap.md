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
