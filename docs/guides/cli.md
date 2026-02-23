# CLI

Semblance provides a CLI for running apps and exporting mocks for frontend integration.

## Run an App

```bash
semblance run <module>:<attr> [--host HOST] [--port PORT] [--reload]
```

The `module:attr` path loads your app. If `attr` has an `as_fastapi()` method (e.g. a `SemblanceAPI` instance), it is called to get the FastAPI app.

**Examples:**

```bash
semblance run app:api --port 8000
semblance run examples.basic.app:api --host 0.0.0.0 --port 8000
semblance run examples.basic.app:app --reload
```

## Export OpenAPI Schema

```bash
semblance export openapi <module>:<attr> [-o FILE] [--examples]
```

- `-o FILE` – write to file (default: stdout)
- `--examples` – call each endpoint (GET, POST, PUT, PATCH, DELETE) and populate response examples from live responses

When your endpoints use `rate_limit`, the generated OpenAPI schema includes a 429 (rate limit exceeded) response description. When `error_rate` and `error_codes` are set, the schema documents those simulated error responses (e.g. 404, 500).

**Example output (truncated):**

```bash
semblance export openapi examples.basic.app:api -o openapi.json
```

```json
{
  "openapi": "3.1.0",
  "paths": {
    "/users": {
      "get": {
        "summary": "List users",
        "responses": {"200": {"description": "Successful response"}}
      }
    }
  }
}
```

## Export Fixtures

```bash
semblance export fixtures <module>:<attr> [-o DIR]
```

Calls each GET, POST, PUT, PATCH, and DELETE endpoint and saves the JSON response to `{output_dir}/{route_id}_{METHOD}.json`. For DELETE responses with status 204, a minimal `{"status": 204}` fixture is written. Also writes `openapi.json`.

**Example:**

```bash
semblance export fixtures examples.basic.app:api -o fixtures
# Creates e.g. fixtures/users_GET.json, fixtures/users_POST.json, fixtures/openapi.json (and PUT/PATCH/DELETE when defined)
```

**Example `fixtures/users_GET.json` (output varies per run):**

```json
[
  {"name": "alice", "created_at": "2021-06-23T16:31:27.650961"},
  {"name": "alice", "created_at": "2024-06-04T03:14:38.140312"},
  {"name": "alice", "created_at": "2020-06-30T11:50:19.723504"},
  {"name": "alice", "created_at": "2023-07-20T08:14:38.140312"},
  {"name": "alice", "created_at": "2021-10-10T03:05:16.140258"}
]
```

## Invalid Paths

If the path is malformed or the module/attribute not found, the CLI exits with an error:

```bash
$ semblance export openapi missing:api
Invalid path 'missing:api'. Use module:attr (e.g. app:api or app:app)
# or
Module 'missing' not found
# or
Attribute 'api' not found in module 'missing'
```
