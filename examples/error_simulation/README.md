# Error Simulation Example

Simulate random API failures with `error_rate` and `error_codes`.

## Code

```python
"""
Error simulation example - error_rate, error_codes.
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


class UserQuery(BaseModel):
    name: str = "alice"


api = SemblanceAPI(seed=99)


@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    list_count=2,
    error_rate=0.3,
    error_codes=[404, 503],
    summary="List users (may fail randomly)",
)
def users():
    """30% of requests return 404 or 503. Use error_rate=0 for tests."""
    pass


app = api.as_fastapi()
```

## Run

```bash
semblance run examples.error_simulation.app:api --port 8000
```

Or with uvicorn (from project root with `PYTHONPATH=.` or `pip install -e .`):

```bash
uvicorn examples.error_simulation.app:app --reload
```

## Try

```bash
# ~70% succeed, ~30% return 404 or 503 (seed=99)
curl "http://127.0.0.1:8000/users?name=alice"
```

Success response (when no error is raised):

```json
[
  {"name": "alice"},
  {"name": "alice"}
]
```

Failure response (when error_rate triggers):

```json
{"detail": "Simulated error"}
```
(Status: 404 or 503)

## Concepts

- **error_rate** – fraction of requests that fail (0.0–1.0)
- **error_codes** – list of status codes to return on failure
- **seed** – use for deterministic testing (same seed → same pattern)
- Use `error_rate=0` in tests for predictable success
