# Request Links (Phase 7)

Bind output fields to the current request: headers and cookies. Use `FromHeader(name)` and `FromCookie(name)` so responses reflect the incoming request.

## FromHeader

Use `FromHeader("Header-Name")` to bind an output field to a request header:

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromHeader, FromInput, SemblanceAPI

class UserResponse(BaseModel):
    name: Annotated[str, FromInput("name")]
    request_id: Annotated[str, FromHeader("X-Request-Id")]

class UserQuery(BaseModel):
    name: str = "alice"

api = SemblanceAPI()
api.get("/user", input=UserQuery, output=UserResponse)(lambda: None)
app = api.as_fastapi()
```

If the client sends `X-Request-Id: abc-123`, the response will include `"request_id": "abc-123"`. If the header is missing, no override is applied and Polyfactory generates a value (so the field is still populated).

## FromCookie

Use `FromCookie("cookie_name")` to bind an output field to a request cookie:

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromCookie, FromInput, SemblanceAPI

class UserResponse(BaseModel):
    name: Annotated[str, FromInput("name")]
    session: Annotated[str, FromCookie("session_id")]

class UserQuery(BaseModel):
    name: str = "alice"

api = SemblanceAPI()
api.get("/user", input=UserQuery, output=UserResponse)(lambda: None)
app = api.as_fastapi()
```

If the client sends a `session_id` cookie, the response will include that value in `session`; otherwise a value is generated.

## When to use

- **Echoing request identity** — e.g. `X-Request-Id`, `X-Correlation-Id`, or session/cookie for debugging or tracing.
- **Testing** — assert that the server “sees” the headers/cookies your client sends.

Request links require request context; they are resolved when building the response inside the handler. They work with `test_client` and normal HTTP; no extra setup.

## See also

- [Request Links example](../examples/request_links.md) — runnable app with headers and cookies.
- [Plugins](plugins.md) — custom link types (e.g. FromEnv) use the same resolution mechanism.
