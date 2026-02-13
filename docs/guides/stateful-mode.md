# Stateful Mode

With `SemblanceAPI(stateful=True)`, POST endpoints store created instances and GET list endpoints return stored data.

## Enabling Stateful Mode

```python
api = SemblanceAPI(stateful=True)
```

## Behavior

- **POST** – Builds the response as usual, stores it in memory, and returns it.
- **GET list** – Returns stored instances for that path instead of generating new ones.

State is keyed by path (e.g. `/users`). It is process-local and not shared across workers.

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
- GET single-item endpoints (e.g. `/users/{id}`) still generate responses; only GET list endpoints read from the store.
