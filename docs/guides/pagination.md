# Pagination

Semblance provides helpers for offset/limit pagination.

## PageParams

Use `PageParams` as a base for your input model to get `limit` and `offset`:

```python
from semblance import PageParams, PaginatedResponse

class UserListQuery(PageParams, BaseModel):
    name: str = "alice"
```

`PageParams` adds `limit: int = 10` and `offset: int = 0`.

## PaginatedResponse

Use `PaginatedResponse[Model]` as the output type:

```python
@api.get("/users", input=UserListQuery, output=PaginatedResponse[User])
def users():
    pass
```

## Response Shape

Responses include `items`, `total`, `limit`, and `offset`:

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

## Example Request

```bash
curl "http://127.0.0.1:8000/users?name=alice&limit=5&offset=10"
```

## Notes

- `total` reflects the simulated total for the current page window.
- In stateless mode, each request generates fresh data. Use `SemblanceAPI(stateful=True)` if you need persistent collections.
