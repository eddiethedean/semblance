# PUT, PATCH, DELETE Example (Phase 5)

Demonstrates non-stateful PUT, PATCH, and DELETE endpoints. Responses are generated from schemas; no persistence.

## Code

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI

class User(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")]

class UpdateBody(BaseModel):
    name: str = "updated"

class PathIdInput(BaseModel):
    id: str = ""

api = SemblanceAPI(seed=42)

@api.put("/users/{id}", input=UpdateBody, output=User)
def put_user():
    pass

@api.patch("/users/{id}", input=UpdateBody, output=User)
def patch_user():
    pass

@api.delete("/users/{id}", input=PathIdInput)
def delete_user():
    pass
```

## Run

```bash
semblance run examples.put_patch_delete.app:api --port 8000
```

## Try

```bash
# PUT – generated response, body merged with path
curl -X PUT http://127.0.0.1:8000/users/abc -H "Content-Type: application/json" -d '{"name":"put-user"}'

# PATCH – same idea
curl -X PATCH http://127.0.0.1:8000/users/xyz -H "Content-Type: application/json" -d '{"name":"patch-user"}'

# DELETE – 204 No Content when no output
curl -X DELETE http://127.0.0.1:8000/users/123
```

Example responses (with `seed=42`):

```json
// PUT /users/abc with body {"name":"put-user"}
{"id": "HbolMJUevblAbkHClEQa", "name": "put-user"}

// PATCH /users/xyz with body {"name":"patch-user"}
{"id": "HbolMJUevblAbkHClEQa", "name": "patch-user"}

// DELETE /users/123 → 204 No Content (no response body)
```

## Concepts

- **Phase 5** — PUT, PATCH, DELETE with input/output models; path params (e.g. `{id}`) are merged with body for response generation.
- **DELETE** — Omit `output` for 204; pass `output=Model` for 200 with a generated body.
- See [Testing](guides/testing.md) for property-based testing and rate limiting.
