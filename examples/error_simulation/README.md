# Error simulation example

Configure opt-in failures with `error_rate` and `error_codes`. A fixed seed makes the selected outcome reproducible.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/error_simulation/app.py)

## Code

```python
"""
Error simulation example - error_rate, error_codes.

Run: semblance run examples.error_simulation.app:api --port 8000
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
    summary="List users with configured error simulation",
)
def users():
    """Unseeded requests have a 30% failure chance; a fixed seed repeats the result."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.error_simulation.app:api --port 8000
```

## Requests and responses

With the bundled `SemblanceAPI(seed=99)`, this request consistently succeeds. The other fixed seeds below reproduce the configured failure responses. To sample failures across repeated requests, use `SemblanceAPI()` without a fixed seed.

**Input 1:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `200 OK`:**

```json
[
  {"name": "alice"},
  {"name": "alice"}
]
```

For this input, restart the example after changing its constructor to `SemblanceAPI(seed=1)`.

**Input 2:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `404 Not Found`:**

```json
{"detail": "Simulated error"}
```

For this input, restart the example after changing its constructor to `SemblanceAPI(seed=8)`.

**Input 3:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice'
```

**Output — `503 Service Unavailable`:**

```json
{"detail": "Simulated error"}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/simulation-options.md) for the behavior and available options.
