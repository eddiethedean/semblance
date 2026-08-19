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

- `total` is the simulated collection size for the request (items generated before applying `offset`/`limit`).
- In stateless mode, each request generates fresh data. Use `SemblanceAPI(stateful=True)` if you need persistent collections.

## PageTable and PageSlice

For a declared token → page map (not adapter page-token codecs), pass `page_table=` and use `PageSlice[Model]` or `list[Model]`. `PaginatedResponse` stays offset/limit and is not valid with `page_table`. `None` is the first page. Unknown tokens return 400 `Invalid page token`. Stateful list GET still serves the table when `page_table` is set.

```python
from semblance import PageSlice, PageTable

class TokenQuery(BaseModel):
    page_token: str | None = None

@api.get(
    "/users",
    input=TokenQuery,
    output=PageSlice[User],
    page_table=PageTable(
        pages={None: [{"name": "a"}], "p2": [{"name": "b"}]},
        next_tokens={None: "p2", "p2": None},
    ),
)
def users():
    pass
```
