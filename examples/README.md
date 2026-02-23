# Semblance Examples

Curated, runnable examples for common use cases. Each example's README shows **example output** from a real run so you can verify behavior.

## Running Examples

From the project root (with semblance installed):

```bash
semblance run examples.<name>.app:api --port 8000
```

Or with uvicorn:

```bash
uvicorn examples.<name>.app:app --reload
```

## Examples

| Example | Description |
|---------|-------------|
| [basic](basic) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](pagination) | PageParams, PaginatedResponse |
| [nested](nested) | Nested model linking |
| [stateful](stateful) | POST stores items, GET returns stored list |
| [advanced](advanced) | WhenInput, ComputedFrom, filter_by |
| [error_simulation](error_simulation) | error_rate, error_codes |
| [plugins](plugins) | Custom link (FromEnv) |
| [put_patch_delete](put_patch_delete) | PUT, PATCH, DELETE (Phase 5) |
| [stateful_crud](stateful_crud) | Full stateful CRUD: GET by id, PUT, PATCH, DELETE (Phase 6) |
| [request_links](request_links) | FromHeader, FromCookie (Phase 7) |
