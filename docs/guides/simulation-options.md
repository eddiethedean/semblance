# Simulation Options

Semblance lets you simulate realistic API behavior: errors, latency, rate limiting, filtering, and optional response validation.

## Error Simulation

Simulate random failures:

```python
@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    error_rate=0.1,
    error_codes=[404, 500],
)
def users():
    pass
```

- `error_rate=0.1` – 10% of requests raise an error.
- `error_codes=[404, 500]` – which status codes to return (default `[404, 500]`).
- Use `error_rate=0` for normal behavior; use `error_rate=1.0` to always fail (useful for tests).
- When `error_rate` and `error_codes` are set, the exported OpenAPI schema documents those simulated error responses.

## Latency and Jitter

Add simulated network delay:

```python
@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    latency_ms=100,
    jitter_ms=20,
)
def users():
    pass
```

Actual delay is `latency_ms ± jitter_ms` milliseconds. Use for load testing or UX simulation.

## Collection Filtering

Filter list items by matching an input field:

```python
@api.get(
    "/users",
    input=UserQueryWithStatus,
    output=list[UserWithStatus],
    filter_by="status",
)
def users():
    pass
```

Only items whose `status` matches `input.status` are returned. Requires the output model to have a `status` field. Oversampling is used internally to approximate the requested list size.

**Example output (`GET /users?name=x&status=active` with `list_count=3`, seed=1):**

```json
[
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"}
]
```

## Rate Limiting

Simulate rate limits per endpoint (sliding 1-second window). When exceeded, the endpoint returns `429 Too Many Requests`:

```python
@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    rate_limit=10,
)
def users():
    pass
```

- `rate_limit=N` — allow at most N requests per second for this (path, method). Additional requests in the same second get 429.
- Per-process, in-memory; suitable for simulation and testing, not distributed production.
- When `rate_limit` is set, the exported OpenAPI schema includes a 429 (rate limit exceeded) response description.

## Response Validation

In development or CI, you can validate that generated responses conform to the output model:

```python
api = SemblanceAPI(validate_responses=True)
```

When `validate_responses=True`, every response is checked with the output model before returning. Schema drift raises a validation error. Adds overhead; use for development or CI, not necessarily in production mocks.

## Combining Options

```python
@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    list_count=5,
    seed_from="seed",
    error_rate=0.05,
    error_codes=[503],
    latency_ms=50,
    jitter_ms=10,
    rate_limit=20,
    filter_by="status",
)
def users():
    pass
```
