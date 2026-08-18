# Foundry Adapter

Unofficial local HTTP simulation of selected [Palantir Foundry API v2](https://www.palantir.com/docs/foundry/api/v2) ontology-read operations, shipped as the independently versioned `semblance-foundry` package.

This adapter is **not affiliated with, endorsed by, or equivalent to Palantir**. It does not implement Foundry's ontology engine, permissions, or compute. It is a test double for client development and CI.

Install it separately from core Semblance:

```bash
pip install semblance-foundry
```

Requires `semblance` 0.6.1 or 0.7.x. Verified against public API v2 documentation dated **2026-08-18**.

## Quick start

```python
from semblance_foundry import FoundryMock, FoundryMockConfig
from semblance_foundry.testing import foundry_test_client

foundry = FoundryMock(FoundryMockConfig(seed=42, auth="optional"))
foundry.load_bundled_fixture()
client = foundry_test_client(foundry)

r = client.get("/api/v2/ontologies/acme/objects/Employee?pageSize=2")
assert r.status_code == 200
```

`load_bundled_fixture()` loads the shipped `acme` ontology. Use `load_fixture(path)` for your own YAML or JSON.

CLI:

```bash
semblance-foundry fixture init --output foundry.yaml
semblance-foundry validate foundry.yaml
semblance-foundry operations
semblance-foundry serve --fixture foundry.yaml --port 8765
```

Omitting `--fixture` serves the bundled `acme` example.

## Auth modes

- `disabled` — ignore `Authorization`
- `optional` (default) — missing token is OK; malformed `Bearer` values return 401
- `strict` — token must be in `FoundryMockConfig.tokens`

Authentication errors never echo the token. This is not an OAuth server and does not validate real Palantir credentials.

## What 0.1.0 covers

| Level | Operations |
|---|---|
| exact | list/get ontologies, object types, objects, linked objects, action types (metadata), query types |
| representative | object search (`eq` / `and` of `eq` only), query execute (static fixture or allow-listed Python callback) |
| unsupported | apply, applyBatch |

Unknown paths return a Foundry-style 404. Apply / applyBatch return `501 UnsupportedOperation` only when `auth=strict`; otherwise 404.

Not in 0.1.0: aggregates, object sets, datasets, transactions, orchestration, streams.

The live compatibility table is also served at `/.well-known/foundry-mock-compatibility.json`.

## Fixtures

YAML/JSON version 1. Extra fields are rejected. Fixtures are data only — no expressions are evaluated. Register query callbacks in Python:

```python
foundry.register_query("employeesByOffice", lambda params, state: {"data": []})
```

## Pagination

List endpoints use `pageSize` / `pageToken` / `nextPageToken`. Tokens are opaque and checksummed. Tampering or cross-resource reuse returns `InvalidPageToken` (400).

## Testing with the official SDK

HTTP contract tests are the required surface. An optional extra pins `foundry-platform-sdk==1.101.0` for localhost compatibility checks; untested SDK versions are not implied compatible.

```bash
pip install "semblance-foundry[sdk]"
pytest packages/semblance-foundry/tests -m sdk
```

## Further reading

- Package README: `packages/semblance-foundry/README.md`
- [Foundry package plan](../semblance_foundry_plan.md) (milestones beyond ontology-read)
