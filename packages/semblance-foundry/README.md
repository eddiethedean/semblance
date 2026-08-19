# semblance-foundry

**Unofficial** local HTTP simulation of selected [Palantir Foundry API v2](https://www.palantir.com/docs/foundry/api/v2) ontology-read operations.

This package is **not affiliated with, endorsed by, or equivalent to Palantir**. It does not implement Foundry's ontology engine, permissions, or compute. It is a test double for client development and CI.

Verified against public API v2 documentation dated **2026-08-18**. See `compatibility.yaml` (also served at `/.well-known/foundry-mock-compatibility.json`).

Requires `semblance` 0.7.x or 0.8.x (`>=0.7.0,<0.9`).

## Install

```bash
pip install semblance-foundry
```

From a clone of this repository:

```bash
pip install -e ".[dev]"
pip install -e "packages/semblance-foundry[dev]"
```

Optional official SDK extra (not installed in default CI):

```bash
pip install "semblance-foundry[sdk]"
pytest packages/semblance-foundry/tests -m sdk
```

Pinned SDK: `foundry-platform-sdk==1.101.0`. Untested SDK versions are not implied compatible.

## Quick start (HTTP)

```python
from semblance_foundry import FoundryMock, FoundryMockConfig
from semblance_foundry.testing import foundry_test_client

foundry = FoundryMock(FoundryMockConfig(seed=42, auth="optional"))
foundry.load_bundled_fixture()
client = foundry_test_client(foundry)

r = client.get("/api/v2/ontologies/acme/objects/Employee?pageSize=2")
assert r.status_code == 200
```

CLI:

```bash
semblance-foundry fixture init --output foundry.yaml
semblance-foundry validate foundry.yaml
semblance-foundry operations
semblance-foundry serve --fixture foundry.yaml --port 8765
# or: semblance-foundry serve   # bundled acme fixture
```

Environment variables for local clients (not Palantir credentials): `SEMBLANCE_FOUNDRY_HOST`, `SEMBLANCE_FOUNDRY_TOKEN`.

## Auth modes

- `disabled` — ignore `Authorization`
- `optional` (default) — missing token is OK; malformed `Bearer` values return 401
- `strict` — token must be in `FoundryMockConfig.tokens`

Authentication errors never echo the token. This is not an OAuth server and does not validate real Palantir credentials.

## Fixtures

YAML/JSON version 1. Extra fields are rejected. Fixtures are **data only** — no expressions are evaluated. Register query callbacks in Python:

```python
foundry.register_query("employeesByOffice", lambda params, state: {"data": []})
```

`load_bundled_fixture()` loads the shipped `acme` example (one ontology, Employee + Office, `worksAt` links, `renameEmployee` action metadata, and `employeesByOffice` static query result). Use `load_fixture(path)` for your own files.

## Pagination

List endpoints use `pageSize` / `pageToken` / `nextPageToken`. Tokens are opaque and checksummed. Tampering or cross-resource reuse returns `InvalidPageToken` (400). Default page size 100, max 1000.

## Known unsupported (0.1.2)

- Action apply / applyBatch — `501 UnsupportedOperation` only when `auth=strict`; otherwise 404
- Aggregates, object sets, datasets, transactions, orchestration, streams
- Search filters other than `eq` and `and` of `eq` (400 `InvalidQuery`)

Unknown paths return Foundry-style 404.

## Compatibility matrix (MVP)

| Level | Operations |
|---|---|
| exact | list/get ontologies, object types, objects, linked objects, action types (metadata), query types |
| representative | object search (`eq`/`and`), query execute (static or callback) |
| unsupported | apply, applyBatch |

## Security

- Do not put production secrets in fixtures or tokens used with this mock
- Tokens are compared in-process and never written to error bodies
- Query/action behavior must be allow-listed Python, never YAML eval

## License

MIT. Palantir and Foundry are trademarks of their respective owners.
