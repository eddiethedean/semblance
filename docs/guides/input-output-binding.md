# Input and Output Binding

This guide covers how to bind output fields to request input using Semblance links.

## FromInput

Bind an output field to an input field by name:

```python
from typing import Annotated
from semblance import FromInput

class User(BaseModel):
    name: Annotated[str, FromInput("name")]
```

When the input has `name="alice"`, the response will have `name: "alice"`. If the input field is missing or `None`, Polyfactory generates a value instead.

Example (with `GET /user?name=alice`):

```json
{"name": "alice"}
```

## DateRangeFrom

Generate a `datetime` within a range defined by two input date fields:

```python
from datetime import datetime
from typing import Annotated
from semblance import DateRangeFrom

class User(BaseModel):
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]
```

If `start_date` and `end_date` are present on the input, `created_at` is a random datetime in that range. When `end <= start`, the result is `start`.

## Input Sources

### Query Parameters (GET)

```python
@api.get("/users", input=UserQuery, output=list[User])
def users():
    pass
```

`UserQuery` is validated from the query string.

### Request Body (POST)

```python
@api.post("/users", input=CreateUserRequest, output=User)
def create_user():
    pass
```

`CreateUserRequest` is validated from the JSON body.

### Path Parameters

```python
class UserGetInput(BaseModel):
    id: str = ""   # default required for query validation
    name: str = "alice"

@api.get("/users/{id}", input=UserGetInput, output=User)
def get_user():
    pass
```

Path params (e.g. `id` from `/users/123`) are merged into the validated input. Your input model must include path param names with defaults.

## Output Types

- **Single model:** `output=User` – one instance
- **List:** `output=list[User]` – list of instances (default 5, configurable)
- **Paginated:** `output=PaginatedResponse[User]` – see [Pagination](pagination.md)

## list_count

Control list length:

```python
# Fixed count
@api.get("/users", input=UserQuery, output=list[User], list_count=10)
def users():
    pass

# From input field
@api.get("/users", input=UserQueryWithLimit, output=list[User], list_count="limit")
def users():
    pass
```
