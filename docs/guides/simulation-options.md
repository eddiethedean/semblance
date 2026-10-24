# Simulation Options

Semblance lets you simulate realistic API behavior: errors, latency, rate limiting, filtering, and optional response validation.

The snippets below extend the models from [Getting started](getting-started.md). Register one version of a route at a time; registering the same method and path twice is an error.

| Behavior to test | Option |
|---|---|
| Fail once, then recover | `scenario=(ScenarioStep(...), ...)` |
| Fail for a particular validated input | `errors=(ErrorCase(...), ...)` |
| Sample failures probabilistically | `error_rate` and `error_codes` |
| Require a known test credential | `bearer_tokens` |
| Delay responses or limit request frequency | `latency_ms`, `jitter_ms`, `rate_limit` |

Normal routes use `error_rate=0`; seeds do not enable errors by themselves.

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

- `error_rate=0.1` gives each unseeded request a 10% chance of raising an error. A short run need not contain exactly 10% failures.
- `error_codes=[404, 500]` – which status codes to return (default `[404, 500]`).
- Use `error_rate=0` for normal behavior; use `error_rate=1.0` to always fail (useful for tests).
- When `error_rate` and `error_codes` are set, the exported OpenAPI schema documents those simulated error responses.

With a fixed global or request seed, error selection restarts from that seed on each request. The same seed therefore repeats the same success or failure status. To sample failures across repeated calls, leave the API unseeded and omit `seed_from`. For a predictable retry test, use [scenario steps](#scenario-steps).

## Bearer tokens

When `bearer_tokens` is set to a non-empty allow-list, the route requires `Authorization: Bearer <token>` matching the list. Missing, malformed, or unknown tokens return 401 `Unauthorized` (the presented token is never echoed). Omit the kwarg (or pass an empty sequence) to leave the route open.

```python
@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    bearer_tokens=("test-token",),
)
def users():
    pass
```

This is independent of Foundry/Databricks adapter auth modes.

## Error maps

`ErrorCase` returns a status and body when a predicate on the validated input matches. First match wins. Schema failures are still 422. Maps run before `error_rate`.

```python
from semblance import ErrorCase

@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    errors=(
        ErrorCase(when=lambda q: q.name == "nobody", status=404, detail="not found"),
    ),
)
def users():
    pass
```

## Scenario steps

`scenario` is a per-route sequence of statuses. After the last step, that step is held (useful for retries). Non-200 steps raise `HTTPException`. 200 continues to normal generation. This is not a replacement for `stateful=True`.

Starting with the getting-started models, save this as `resilience.py`:

```python
from app import User, UserQuery
from semblance import ScenarioStep, SemblanceAPI

api = SemblanceAPI(seed=42)

@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    list_count=2,
    scenario=(
        ScenarioStep(status=503, detail="busy"),
        ScenarioStep(status=200),
    ),
)
def users():
    pass
```

Run `semblance run resilience:api --port 8001`. Send the same request twice:

```bash
curl "http://127.0.0.1:8001/users?name=alice"
```

**First output — `503 Service Unavailable`:**

```json
{"detail": "busy"}
```

**Second output — `200 OK`:**

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Later requests keep succeeding. Scenario progress belongs to the API instance and is shared across requests to that route and method; construct a fresh instance to restart it. Clearing the resource store does not reset a scenario.

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
