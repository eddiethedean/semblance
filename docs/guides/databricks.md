# Databricks Adapter

Unofficial local HTTP simulation of selected [Databricks workspace REST](https://docs.databricks.com/api/workspace/) operations, shipped as the independently versioned `semblance-databricks` package.

This adapter is **not affiliated with, endorsed by, or equivalent to Databricks**. It does not run Spark, jobs, or SQL engines. It is a test double for client development and CI.

Install it separately from core Semblance:

```bash
pip install semblance-databricks
```

Requires `semblance` 0.7.x. Verified against public workspace REST documentation dated **2026-08-19**.

## Quick start

```python
from semblance_databricks import DatabricksMock, DatabricksMockConfig
from semblance_databricks.testing import databricks_test_client

dbx = DatabricksMock(DatabricksMockConfig(seed=42, auth="optional"))
dbx.load_bundled_fixture()
client = databricks_test_client(dbx)

r = client.get("/api/2.1/clusters/list?page_size=2")
assert r.status_code == 200
```

`load_bundled_fixture()` loads the shipped `acme` workspace. Use `load_fixture(path)` for your own YAML or JSON. Advance cluster and run state with `dbx.tick()`.

CLI (default port **8766**):

```bash
semblance-databricks fixture init --output databricks.yaml
semblance-databricks validate databricks.yaml
semblance-databricks operations
semblance-databricks serve --fixture databricks.yaml --port 8766
```

Omitting `--fixture` serves the bundled `acme` example.

## Auth modes

- `disabled` — ignore `Authorization`
- `optional` (default) — missing token is OK; malformed `Bearer` values return 401
- `strict` — token must be in `DatabricksMockConfig.tokens`

Authentication errors never echo the token. This is not an OAuth server and does not validate real Databricks credentials.

## What 0.1.0 covers

Phases A–D from the [Databricks package plan](../semblance_databricks_plan.md): cluster/job/run reads, writes and virtual-clock lifecycle, warehouses, secrets **metadata only**, DBFS stubs, libraries/events, permissions, SQL statement chunks (no Spark).

Unknown paths return a Databricks-style 404. Known stubs (`permanent-delete`, `dbfs/add-block`) return `501 FEATURE_DISABLED` only when `auth=strict`; otherwise 404.

Jobs primary paths are **2.2**. Optional `/api/2.1/jobs/...` aliases are representative. Secret **values** are never returned on REST.

The live compatibility table is served at `/.well-known/semblance-databricks-compat.json`.

## Testing with the official SDK

HTTP contract tests are the required surface. An optional extra pins `databricks-sdk==0.57.0` for localhost compatibility checks; untested SDK versions are not implied compatible.

```bash
pip install "semblance-databricks[sdk]"
pytest packages/semblance-databricks/tests -m sdk
```

## Further reading

- Package README: `packages/semblance-databricks/README.md`
- [Databricks package plan](../semblance_databricks_plan.md)
