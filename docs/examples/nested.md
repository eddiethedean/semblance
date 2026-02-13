# Nested Model Example

Output models with nested structures. Links propagate into nested models.

## Run

```bash
semblance run examples.nested.app:api --port 8000
```

## Try

```bash
curl "http://127.0.0.1:8000/user?name=foo&city=Boston"
```

Example response:

```json
{
  "name": "foo",
  "address": {
    "street": "",
    "city": "Boston",
    "zip": ""
  }
}
```

`city` comes from the query; `street` and `zip` are generated (or use defaults).

## Concepts

- **Nested models** – `UserWithAddress` contains `Address`
- **Links in nested fields** – `city` in `Address` uses `FromInput("city")`
- Resolver traverses nested models to apply links
