# Request Links Example (Phase 7)

Output fields bound to the current request: `FromHeader("X-Request-Id")` and `FromCookie("session_id")`. Responses echo headers and cookies when present.

## Code

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromCookie, FromHeader, FromInput, SemblanceAPI

class UserQuery(BaseModel):
    name: str = "alice"

class UserResponse(BaseModel):
    name: Annotated[str, FromInput("name")]
    request_id: Annotated[str, FromHeader("X-Request-Id")]
    session: Annotated[str, FromCookie("session_id")]

api = SemblanceAPI(seed=42)
api.get("/user", input=UserQuery, output=UserResponse)(lambda: None)
app = api.as_fastapi()
```

## Run

```bash
semblance run examples.request_links.app:api --port 8000
```

## Try

```bash
# With header and cookie
curl -i "http://127.0.0.1:8000/user?name=alice" \
  -H "X-Request-Id: req-abc-123" \
  -H "Cookie: session_id=sess-xyz"

# Response includes "request_id": "req-abc-123", "session": "sess-xyz"
# If header/cookie missing, those fields get generated values.
```

## Concepts

- **Phase 7** — Built-in request links: `FromHeader(name)` and `FromCookie(name)`.
- Resolved at response build time from the current request; works with `test_client` and live servers.
- See [Request Links](guides/request-links.md) for details.
