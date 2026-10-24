# Pagination Example

List endpoint with `PageParams` and `PaginatedResponse`.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/pagination/app.py)

## Code

```python
"""
Pagination example - PageParams and PaginatedResponse.

Run: semblance run examples.pagination.app:api --port 8000
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.pagination.app:api --port 8000
```

## Requests and responses

This example generates a pool of `limit` items, so `limit=3` and `offset=0` return three items with `total=3`.

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/users?limit=3&offset=0&name=alice'
```

**Output — `200 OK`:**

```json
{
  "items": [
    {
      "name": "alice"
    },
    {
      "name": "alice"
    },
    {
      "name": "alice"
    }
  ],
  "total": 3,
  "limit": 3,
  "offset": 0
}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/pagination.md) for the behavior and available options.
