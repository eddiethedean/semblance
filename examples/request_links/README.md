# Request Links Example

Output fields bound to the current request: `FromHeader("X-Request-Id")` and `FromCookie("session_id")`. Responses echo headers and cookies when present.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/request_links/app.py)

## Code

```python
"""
Phase 7 example: Request links — FromHeader, FromCookie.

Run: semblance run examples.request_links.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromCookie, FromHeader, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    """Query params for user endpoint."""

    name: str = "alice"


class UserResponse(BaseModel):
    """Response with request-bound fields."""

    name: Annotated[str, FromInput("name")]
    request_id: Annotated[str, FromHeader("X-Request-Id")]
    session: Annotated[str, FromCookie("session_id")]


api = SemblanceAPI(seed=42)


@api.get(
    "/user",
    input=UserQuery,
    output=UserResponse,
    summary="Get user (echoes header and cookie)",
)
def get_user():
    """request_id comes from X-Request-Id header; session from session_id cookie."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.request_links.app:api --port 8000
```

## Requests and responses

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/user?name=alice' -H 'X-Request-Id: id-1' -H 'Cookie: session_id=sess-1'
```

**Output — `200 OK`:**

```json
{"name": "alice", "request_id": "id-1", "session": "sess-1"}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/request-links.md) for the behavior and available options.
