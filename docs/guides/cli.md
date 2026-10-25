# CLI and configuration

Use the `semblance` command to scaffold a simulator, validate route links, serve the app, and export its schema or sample responses. Run commands from a directory where the target Python module can be imported.

## Command reference

| Command | Result |
|---|---|
| `semblance init --with-config` | Create `app.py` and `semblance.yaml` in the current directory |
| `semblance validate app:api` | Validate route bindings; print `OK` and exit 0 on success |
| `semblance run app:api --port 8000` | Serve a `SemblanceAPI` using Uvicorn |
| `semblance run app:app --reload` | Serve an exported FastAPI instance with automatic reload |
| `semblance export openapi app:api -o openapi.json` | Write the OpenAPI schema |
| `semblance export fixtures app:api -o fixtures` | Write successful sample responses and `openapi.json` |

Use `semblance --help` or a subcommand's `--help` for the complete argument list.

## Scaffold an app

In a new directory:

```bash
semblance init --with-config
```

The command writes `app.py` and `semblance.yaml`, then prints a run command. `--with-config` has the short form `-c`. Use `--force` to overwrite existing scaffold files.

The configuration file is optional. To load it, use `SemblanceAPI.from_config()` or an explicit `config_path` as described below.

## Validate before serving

```bash
semblance validate app:api
```

The target must be a `SemblanceAPI`. Successful validation prints `OK`; invalid routes or field links exit with status 1. This checks bindings such as `FromInput("name")` against the input model without starting a server.

You can also enable startup checks with `SemblanceAPI(validate_links=True)`.

## Run an app

```bash
semblance run app:api --host 127.0.0.1 --port 8000
```

`app:api` means the `api` object in the importable `app` module. The CLI calls `as_fastapi()` when the target exposes it. You can pass only a module name when it contains exactly one public `SemblanceAPI` or FastAPI instance.

For reload, export a FastAPI instance in your module:

```python
app = api.as_fastapi()
```

Then run:

```bash
semblance run app:app --port 8000 --reload
```

Reload requires the FastAPI instance target; `app:api --reload` is rejected. The [getting-started app](getting-started.md) already exports both objects.

## Export OpenAPI

Export commands use FastAPI's test-client support, including when exporting live examples. Install the `httpx2`-compatible FastAPI and Starlette versions:

```bash
pip install httpx2 "fastapi>=0.133.0" "starlette>=1.3.1"
semblance export openapi app:api -o openapi.json
```

**Output:** `Wrote openapi.json`. Omit `-o` to print the schema to stdout. The schema includes request and response models, route metadata, and configured error or rate-limit responses.

Add successful live samples:

```bash
semblance export openapi app:api -o openapi.json --examples
```

The exporter sends minimal requests: empty JSON for POST/PUT/PATCH, default query values, and `1` for path parameters. Routes that require additional input or authentication may not produce a successful sample. For stateful routes or scenarios, sampling can change the in-memory state used during that export.

## Export fixtures

Using `app.py` from [Getting started](getting-started.md):

```bash
semblance export fixtures app:api -o fixtures
```

**Output:** `Wrote fixtures to fixtures`. This app produces:

```text
fixtures/
├── openapi.json
└── users_GET.json
```

The contents of `users_GET.json` are:

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Files use `{route_id}_{METHOD}.json`; for example, `/users/{id}` becomes `users_id_GET.json`. The same minimal-request rules apply as for OpenAPI examples. DELETE routes sampled with HTTP 204 get a `{"status":204}` fixture marker. Failed DELETE samples are skipped, and any stale DELETE fixture from an earlier export is removed.

## Configuration

Use YAML defaults in **`semblance.yaml`**:

```yaml
seed: 42
list_count: 2
stateful: false
validate_links: true
validate_responses: true
verbose_errors: false
```

YAML loading requires `pip install pyyaml`. Load the file explicitly:

```python
from semblance import SemblanceAPI

api = SemblanceAPI(config_path="semblance.yaml")
```

Or use discovery, with optional keyword overrides:

```python
from semblance import SemblanceAPI

api = SemblanceAPI.from_config(list_count=3)
```

Discovery looks in the current directory, then its parent, for `semblance.yaml`, `semblance.yml`, or a `[tool.semblance]` section in `pyproject.toml`. At each location YAML is checked first. A plain `SemblanceAPI()` uses constructor defaults and does not discover files.

The TOML equivalent is:

```toml
[tool.semblance]
seed = 42
list_count = 2
stateful = false
validate_links = true
validate_responses = true
verbose_errors = false
```

Python 3.10 needs `pip install tomli` for TOML loading; Python 3.11+ includes `tomllib`.

## Troubleshooting imports

If the CLI reports a missing module, run it from the directory containing that module or install the package containing it. Use an explicit target such as `app:api` when a module exports multiple app objects. See [Troubleshooting](troubleshooting.md#module-attr-not-found).
