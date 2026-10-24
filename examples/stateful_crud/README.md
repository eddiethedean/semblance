# Stateful CRUD Example

Full CRUD with in-memory store: POST creates, GET list returns stored items, GET by id / PUT / PATCH / DELETE operate on stored resources.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/stateful_crud/app.py)

## Code

```python
"""
Phase 6 example: Full stateful CRUD — POST, GET list, GET by id, PUT, PATCH, DELETE.

Run: semblance run examples.stateful_crud.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class CreateUser(BaseModel):
    """POST body for creating a user."""

    name: str = "alice"


class UserWithId(BaseModel):
    """User with id; used for list and by-id responses."""

    id: str = ""
    name: Annotated[str, FromInput("name")]


class UpdateBody(BaseModel):
    """Request body for PUT and PATCH."""

    name: str = "updated"


class PathIdInput(BaseModel):
    """Path parameter for by-id routes."""

    id: str = ""


api = SemblanceAPI(stateful=True, seed=42)


@api.post("/users", input=CreateUser, output=UserWithId, summary="Create user")
def create_user():
    """Stores created user; returns instance with generated id."""
    pass


@api.get("/users", input=CreateUser, output=list[UserWithId], summary="List users")
def list_users():
    """Returns all stored users."""
    pass


@api.get(
    "/users/{id}",
    input=PathIdInput,
    output=UserWithId,
    summary="Get user by id",
)
def get_user():
    """Returns stored user or 404."""
    pass


@api.put(
    "/users/{id}",
    input=UpdateBody,
    output=UserWithId,
    summary="Upsert user",
)
def put_user():
    """Replaces existing or adds new user with this id."""
    pass


@api.patch(
    "/users/{id}",
    input=UpdateBody,
    output=UserWithId,
    summary="Update user",
)
def patch_user():
    """Updates existing user; 404 if not found."""
    pass


@api.delete(
    "/users/{id}",
    input=PathIdInput,
    summary="Delete user",
)
def delete_user():
    """Removes user; 204 if found, 404 if not."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.stateful_crud.app:api --port 8000
```

## Requests and responses

Run against a fresh server, in the order shown. Use the ID returned by POST in subsequent paths; the sample below uses `HbolMJUevblAbkHClEQa`.

**Input 1:**

```bash
curl -sS -X POST http://127.0.0.1:8000/users -H 'Content-Type: application/json' -d '{"name": "alice"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
```

**Input 2:**

```bash
curl -sS http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}
```

**Input 3:**

```bash
curl -sS -X PUT http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa -H 'Content-Type: application/json' -d '{"name": "alice-replaced"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice-replaced"}
```

**Input 4:**

```bash
curl -sS -X PATCH http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa -H 'Content-Type: application/json' -d '{"name": "alice-updated"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "alice-updated"}
```

**Input 5:**

```bash
curl -sS http://127.0.0.1:8000/users
```

**Output — `200 OK`:**

```json
[
  {"id": "HbolMJUevblAbkHClEQa", "name": "alice-updated"}
]
```

**Input 6:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `204 No Content`:**

No response body.

**Input 7:**

```bash
curl -sS http://127.0.0.1:8000/users/HbolMJUevblAbkHClEQa
```

**Output — `404 Not Found`:**

```json
{"detail": "Not found"}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/stateful-mode.md) for the behavior and available options.
