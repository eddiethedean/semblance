# Simulation Options

Semblance lets you simulate realistic API behavior: errors, latency, and filtering.

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
    filter_by="status",
)
def users():
    pass
```
