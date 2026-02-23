# Stateful Mode

With `SemblanceAPI(stateful=True)`, POST endpoints store created instances and GET list endpoints return stored data.

## Enabling Stateful Mode

```python
api = SemblanceAPI(stateful=True)
```

## Behavior

- **POST** – Builds the response as usual, stores it in memory, and returns it.
- **GET list** – Returns stored instances for that path instead of generating new ones.
- **GET single (by id)** – For routes with a path parameter (e.g. `/users/{id}`), returns the stored item whose id matches the path param, or 404 if not found. The store key is the *collection path* (e.g. `/users`), derived by stripping the last `/{param}` segment.
- **PUT** – When stateful and the path has a path param (e.g. `/users/{id}`): if an item with that id exists, it is replaced with the built response (id set from path); otherwise the response is added. Returns the upserted instance.
- **PATCH** – When stateful and the path has a path param: looks up the item by id; if not found, returns 404. Otherwise replaces it with the built response (id set from path) and returns the updated instance.
- **DELETE** – When stateful and the path has a path param: removes the item with that id from the store. Returns 204 if found, 404 if not found.

State is keyed by *collection path* (e.g. `/users`). Paths like `/users/{id}` map to the collection `/users`; the path param name (e.g. `id`) is used as the field for lookups. It is process-local and not shared across workers.

## Example

```python
from typing import Annotated
from semblance import FromInput, SemblanceAPI

class CreateUser(BaseModel):
    name: str

class UserWithId(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")]

api = SemblanceAPI(stateful=True)
api.post("/users", input=CreateUser, output=UserWithId)(lambda: None)
api.get("/users", input=CreateUser, output=list[UserWithId])(lambda: None)
app = api.as_fastapi()
```

```bash
# Create users
curl -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d '{"name":"alice"}'
curl -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d '{"name":"bob"}'

# List returns stored users
curl http://127.0.0.1:8000/users
```

Example responses (IDs are auto-generated UUIDs):

```json
// POST alice
{"id": "HbolMJUevblAbkHClEQa", "name": "alice"}

// POST bob
{"id": "PKriXrefSFPLBYtCRGSE", "name": "bob"}

// GET /users
[
  {"id": "HbolMJUevblAbkHClEQa", "name": "alice"},
  {"id": "PKriXrefSFPLBYtCRGSE", "name": "bob"}
]
```

## ID Generation

If the output model has an `id` field and it is empty or missing, Semblance assigns a UUID before storing.

## Clearing State

Use `clear_store()` for tests or resets:

```python
api.clear_store()        # Clear all paths
api.clear_store("/users")  # Clear only /users
```

## Limitations

- State lives in process memory; it is lost on restart.
- Not suitable for multi-worker deployments; each worker has its own store.
- For stateful by-id behavior, use a single path parameter (e.g. `{id}`); the first path param is used as the id field for store lookups.
