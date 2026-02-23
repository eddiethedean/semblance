# API Reference

## Core

### SemblanceAPI

`from semblance import SemblanceAPI`

Main API builder. Register endpoints with input/output models.

```python
api = SemblanceAPI(seed=None, stateful=False, validate_responses=False)
api.get(path, *, input, output, list_count=5, seed_from=..., error_rate=0, error_codes=..., latency_ms=0, jitter_ms=0, filter_by=..., rate_limit=..., summary=..., description=..., tags=...)
api.post(path, *, input, output, ...)   # same options as get
api.put(path, *, input, output, ...)    # same options as post
api.patch(path, *, input, output, ...)  # same options as post
api.delete(path, *, input, output=None) # output=None → 204 No Content; else 200 with body
app = api.as_fastapi()
```

- **validate_responses** — when `True`, validates every generated response against the output model (for dev/CI).
- **rate_limit** — optional; max requests per second per endpoint (returns 429 when exceeded).

### Links

`from semblance import FromInput, DateRangeFrom, WhenInput, ComputedFrom`

- **FromInput(field)** — bind output field to input field by name
- **DateRangeFrom(start, end)** — datetime in range defined by input date fields
- **WhenInput(cond_field, cond_value, then_link)** — apply link when condition matches
- **ComputedFrom(fields, fn)** — compute field from other output fields

### Pagination

`from semblance import PageParams, PaginatedResponse`

- **PageParams** — limit, offset query params
- **PaginatedResponse[T]** — items, total, limit, offset

### Plugins

`from semblance import register_link, LinkProtocol`

- **register_link(LinkClass)** — register custom link type
- **LinkProtocol** — protocol for custom links (must implement `resolve(input_data, rng)`)

### Testing

`from semblance import test_client`

- **test_client(app)** — httpx TestClient for FastAPI app

### Property-based Testing

`from semblance.property_testing import strategy_for_input_model, test_endpoint`

- **strategy_for_input_model(model, path_template=None)** — Hypothesis strategy that generates instances of the input model (for GET query or POST/PUT/PATCH body).
- **test_endpoint(client, method, path, input_strategy, output_model, path_params=..., validate_response=True, invariants=())** — runs a property-based test: draws input, calls endpoint, validates response; optional invariants (input, output) → bool.

Requires `hypothesis` (included in `[dev]`).

## CLI

```bash
semblance run app:api [--host HOST] [--port PORT] [--reload]
semblance export openapi app:api [-o FILE] [--examples]
semblance export fixtures app:api [-o DIR]
```
