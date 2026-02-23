# CLI

Semblance provides a CLI for running apps, validating config, and exporting mocks for frontend integration.

## Init (scaffold app)

```bash
semblance init [-c] [--force]
```

Creates a minimal `app.py` in the current directory. Use `-c` / `--with-config` to also write `semblance.yaml` with commented defaults. Use `--force` to overwrite existing `app.py`.

**Example output:**

```
Wrote app.py
Run: semblance run app:api --port 8000
```

## Validate (no server)

```bash
semblance validate <module>:<attr>
```

Validates routes and link bindings (e.g. `FromInput("typo")` on a missing field) without starting a server. Exit 0 if valid, 1 otherwise. Useful in CI or pre-commit. The target must be a SemblanceAPI (module:attr with `get_endpoint_specs`).

**Example:**

```bash
semblance validate examples.basic.app:api
# OK
```

## Run an App

```bash
semblance run <module>[:<attr>] [--host HOST] [--port PORT] [--reload]
```

You can pass `module:attr` (e.g. `app:api`) or just `module` when there is a single candidate (e.g. one `SemblanceAPI` or FastAPI app in the module). If `attr` has an `as_fastapi()` method (e.g. a `SemblanceAPI` instance), it is called to get the FastAPI app.

**Examples:**

```bash
semblance run app:api --port 8000
semblance run app --port 8000
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

**Example `fixtures/users_GET.json`** (with `examples.basic.app:api`, which uses `seed=42` and `list_count=2`):

```json
[
  {"name": "alice", "created_at": "2024-08-21T09:22:43.516168"},
  {"name": "alice", "created_at": "2024-01-10T03:05:39.176702"}
]
```

Without a fixed seed, output varies per run.

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
