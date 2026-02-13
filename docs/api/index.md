# API Reference

## Core

### SemblanceAPI

`from semblance import SemblanceAPI`

Main API builder. Register endpoints with input/output models.

```python
api = SemblanceAPI(seed=None, stateful=False)
api.get(path, *, input, output, ...)
api.post(path, *, input, output, ...)
app = api.as_fastapi()
```

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

## CLI

```bash
semblance run app:api [--host HOST] [--port PORT] [--reload]
semblance export openapi app:api [-o FILE] [--examples]
semblance export fixtures app:api [-o DIR]
```
