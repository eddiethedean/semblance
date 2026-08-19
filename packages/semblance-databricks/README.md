# semblance-databricks

**Unofficial** local HTTP simulation of selected [Databricks workspace REST](https://docs.databricks.com/api/workspace/) operations (clusters, jobs, warehouses, secrets metadata, DBFS stubs, permissions, SQL statements).

This package is **not affiliated with, endorsed by, or equivalent to Databricks**. It does not run Spark, jobs, or SQL engines. It is a test double for client development and CI.

Verified against public workspace REST documentation dated **2026-08-19**. See `compatibility.yaml` (also served at `/.well-known/semblance-databricks-compat.json`).

Requires `semblance` 0.7.x or 0.8.x (`>=0.7.0,<0.9`).

## Install

```bash
pip install semblance-databricks
```

From a clone of this repository:

```bash
pip install -e ".[dev]"
pip install -e "packages/semblance-databricks[dev]"
```

Optional official SDK extra (not installed in default CI):

```bash
pip install "semblance-databricks[sdk]"
pytest packages/semblance-databricks/tests -m sdk
```

Pinned SDK: `databricks-sdk==0.57.0`. Untested SDK versions are not implied compatible.

## Quick start (HTTP)

```python
from semblance_databricks import DatabricksMock, DatabricksMockConfig
from semblance_databricks.testing import databricks_test_client

dbx = DatabricksMock(DatabricksMockConfig(seed=42, auth="optional"))
dbx.load_bundled_fixture()
client = databricks_test_client(dbx)

r = client.get("/api/2.1/clusters/list?page_size=2")
assert r.status_code == 200
```

CLI:

```bash
semblance-databricks fixture init --output databricks.yaml
semblance-databricks validate databricks.yaml
semblance-databricks operations
semblance-databricks serve --fixture databricks.yaml --port 8766
# or: semblance-databricks serve   # bundled acme fixture
```

Environment variables for local clients (not Databricks credentials): `SEMBLANCE_DATABRICKS_HOST`, `SEMBLANCE_DATABRICKS_TOKEN`.

## Auth modes

- `disabled` — ignore `Authorization`
- `optional` (default) — missing token is OK; malformed `Bearer` values return 401
- `strict` — token must be in `DatabricksMockConfig.tokens`

Authentication errors never echo the token. This is not an OAuth server.

## Fixtures

YAML/JSON version 1. Extra fields are rejected. Fixtures are **data only**. Secret **values** are never returned on REST (list and put only; there is no get-key).

`load_bundled_fixture()` loads the shipped `acme` workspace. Use `load_fixture(path)` for your own files. Advance cluster/run state with `dbx.tick()`.

## Pagination

List endpoints use `page_size` or `limit` plus `page_token` / `next_page_token`. Tokens are opaque and checksummed. Tampering returns 400 `INVALID_PARAMETER_VALUE`.

## Known unsupported (0.1.0)

- Unity Catalog, Model Serving, DLT / Spark Declarative Pipelines
- Jobs API 2.0 as primary (optional 2.1 aliases are representative)
- Real Spark/SQL execution (statements use fixture or allow-listed callbacks)

Unknown paths return Databricks-style 404. Known stubs such as `clusters/permanent-delete` and `dbfs/add-block` return 501 only when `auth=strict`.

## Security

- Do not put production secrets in fixtures or tokens used with this mock
- Tokens are compared in-process and never written to error bodies
- Query/SQL/run-output behavior must be allow-listed Python, never YAML eval

## License

MIT. Databricks is a trademark of its respective owners.
