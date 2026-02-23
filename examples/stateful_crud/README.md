# Stateful CRUD Example (Phase 6)

Full CRUD with in-memory store: POST creates, GET list returns stored items, GET by id / PUT / PATCH / DELETE operate on stored resources.

## Code

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI

class CreateUser(BaseModel):
    name: str = "alice"

class UserWithId(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")]

class UpdateBody(BaseModel):
    name: str = "updated"

class PathIdInput(BaseModel):
    id: str = ""

api = SemblanceAPI(stateful=True, seed=42)

@api.post("/users", input=CreateUser, output=UserWithId)
def create_user():
    pass

@api.get("/users", input=CreateUser, output=list[UserWithId])
def list_users():
    pass

@api.get("/users/{id}", input=PathIdInput, output=UserWithId)
def get_user():
    pass

@api.put("/users/{id}", input=UpdateBody, output=UserWithId)
def put_user():
    pass

@api.patch("/users/{id}", input=UpdateBody, output=UserWithId)
def patch_user():
    pass

@api.delete("/users/{id}", input=PathIdInput)
def delete_user():
    pass

app = api.as_fastapi()
```

## Run

```bash
semblance run examples.stateful_crud.app:api --port 8000
```

## Try

```bash
# Create two users
curl -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d '{"name":"alice"}'
curl -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d '{"name":"bob"}'

# List (returns stored)
curl http://127.0.0.1:8000/users

# Get by id (use an id from list)
curl http://127.0.0.1:8000/users/<id>

# PUT upsert (create or replace)
curl -X PUT http://127.0.0.1:8000/users/new-1 -H "Content-Type: application/json" -d '{"name":"created"}'

# PATCH update (404 if missing)
curl -X PATCH http://127.0.0.1:8000/users/new-1 -H "Content-Type: application/json" -d '{"name":"updated"}'

# DELETE
curl -X DELETE http://127.0.0.1:8000/users/new-1
```

## Concepts

- **Phase 6** — Stateful GET by id, PUT (upsert), PATCH (update), DELETE (remove) keyed by path param (e.g. `id`).
- Collection path is derived from the route (e.g. `/users/{id}` → store key `/users`).
- See [Stateful Mode](guides/stateful-mode.md) for details.
