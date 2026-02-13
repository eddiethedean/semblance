# Pagination Example

List endpoint with `PageParams` and `PaginatedResponse`.

## Code

```python
"""
Pagination example - PageParams and PaginatedResponse.
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, PageParams, PaginatedResponse, SemblanceAPI


class UserQuery(PageParams, BaseModel):
    """Query with limit and offset."""

    name: str = "alice"


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI(seed=42)


@api.get(
    "/users",
    input=UserQuery,
    output=PaginatedResponse[User],
    list_count="limit",
    summary="List users (paginated)",
)
def users():
    """Returns paginated user list."""
    pass


app = api.as_fastapi()
```

## Run

```bash
semblance run examples.pagination.app:api --port 8000
```

## Try

```bash
curl "http://127.0.0.1:8000/users?limit=5&offset=0&name=alice"
curl "http://127.0.0.1:8000/users?limit=3&offset=10"
```

Example response (`limit=3&offset=0`):

```json
{
  "items": [
    {"name": "alice"},
    {"name": "alice"},
    {"name": "alice"}
  ],
  "total": 3,
  "limit": 3,
  "offset": 0
}
```

## Concepts

- **PageParams** – `limit` and `offset` query params
- **PaginatedResponse[T]** – `items`, `total`, `limit`, `offset`
