# Pagination Example

List endpoint with `PageParams` and `PaginatedResponse`.

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
