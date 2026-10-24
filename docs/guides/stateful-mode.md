# Stateful mode

Enable `SemblanceAPI(stateful=True)` to keep resources between requests in the same process. POST stores generated responses, and GET list routes return the stored collection.

## Behavior by method

| Method | Stateful behavior |
|---|---|
| POST `/users` | Generates a response and adds it to `/users` |
| GET `/users` | Returns the stored collection, initially empty |
| GET `/users/{id}` | Returns the first matching item, or 404 |
| PUT `/users/{id}` | Replaces an existing item or adds a new one, using the path ID |
| PATCH `/users/{id}` | Replaces an existing item with a generated response, using the path ID; returns 404 when missing |
| DELETE `/users/{id}` | Removes the item and returns 204, or 404 when missing |

PATCH builds a new response from the supplied model. Model defaults and generated fields can replace existing values; it does not merge arbitrary omitted fields into the previous record.

## A complete CRUD API

This example takes IDs from the request so each created user has an explicit identity. Save it as **`stateful.py`**:

```python
from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class EmptyQuery(BaseModel):
    pass


class UserInput(BaseModel):
    id: int = 0
    name: str


class PathId(BaseModel):
    id: int = 0


class User(BaseModel):
    id: Annotated[int, FromInput("id")]
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI(stateful=True, seed=42)


@api.post("/users", input=UserInput, output=User)
def create_user():
    pass


@api.get("/users", input=EmptyQuery, output=list[User])
def list_users():
    pass


@api.get("/users/{id}", input=PathId, output=User)
def get_user():
    pass


@api.put("/users/{id}", input=UserInput, output=User)
def replace_user():
    pass


@api.patch("/users/{id}", input=UserInput, output=User)
def update_user():
    pass


@api.delete("/users/{id}", input=PathId)
def delete_user():
    pass
```

Run it:

```bash
semblance run stateful:api --port 8000
```

## Create and read

**Input:**

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"id":101,"name":"alice"}'
```

**Output — `200 OK`:**

```json
{"id": 101, "name": "alice"}
```

**Input:**

```bash
curl http://127.0.0.1:8000/users
```

**Output — `200 OK`:**

```json
[{"id": 101, "name": "alice"}]
```

**Input:**

```bash
curl http://127.0.0.1:8000/users/101
```

**Output — `200 OK`:**

```json
{"id": 101, "name": "alice"}
```

## Replace, update, and delete

Run these requests against the same server, after creating user 101:

| Input | JSON body | Output |
|---|---|---|
| PUT `/users/101` | `{"name":"bob"}` | `200` with `{"id":101,"name":"bob"}` |
| PATCH `/users/101` | `{"name":"robert"}` | `200` with `{"id":101,"name":"robert"}` |
| DELETE `/users/101` | No body | `204 No Content`, empty body |
| GET `/users/101` | No body | `404` with `{"detail":"Not found"}` |
| GET `/users` | No body | `200` with `[]` |

For example, the PATCH request is:

```bash
curl -X PATCH http://127.0.0.1:8000/users/101 \
  -H "Content-Type: application/json" \
  -d '{"name":"robert"}'
```

## IDs and collection paths

The store groups routes by collection path. `/users/{id}` maps to `/users`, and the first path parameter's name supplies the field used for lookup. Give path fields a default in the input model so validation can run before the path value is merged.

If a generated response has a missing or empty `id`, the store assigns a UUID. A plain `id: str` can already have a generated string, so IDs are not always UUIDs. Fixed seeds can repeat those generated IDs; when distinct identities matter, bind an explicit ID from the request as this guide does, or create resources through PUT with distinct path IDs.

## Reset and inspect state

Clear all collections or just one:

```python
api.clear_store()
api.clear_store("/users")
```

Enable `SemblanceAPI(stateful=True, verbose_errors=True)` to include collection and ID information in stateful 404 details.

State lives in process memory and is lost on restart. Each worker has its own store. Use a single path parameter for by-ID routes.

A [scenario](simulation-options.md#scenario-steps) advances a sequence of statuses; it does not store resources. Use stateful mode for resource data and scenarios for failure and recovery behavior.
