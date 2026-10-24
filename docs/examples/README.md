# Runnable examples

Each example includes its models, startup command, requests, and sample responses. Run the examples from a checkout of the repository:

```bash
git clone https://github.com/eddiethedean/semblance.git
cd semblance
pip install -e .
```

Start one example at a time. For example:

```bash
semblance run examples.basic.app:api --port 8000
```

Send requests from a second terminal. The server exposes interactive API docs at [localhost:8000/docs](http://127.0.0.1:8000/docs). When an example has `app = api.as_fastapi()`, use `semblance run examples.basic.app:app --reload` for automatic reload.

## Choose an example

| Example | What it demonstrates |
|---|---|
| [Basic](basic.md) | Query binding and timestamps within an input date range |
| [Pagination](pagination.md) | Offset, limit, and the paginated response envelope |
| [Nested models](nested.md) | Links inside a nested response model |
| [Advanced links](advanced.md) | Conditional fields, computed values, and collection filtering |
| [Stateful collections](stateful.md) | POST results kept for subsequent GET requests |
| [Stateful CRUD](stateful_crud.md) | Lookup, replacement, update, and deletion by ID |
| [PUT, PATCH, DELETE](put_patch_delete.md) | Generated responses for write methods |
| [Request links](request_links.md) | Values copied from headers and cookies |
| [Custom links](plugins.md) | A field supplied by an environment variable |
| [Error simulation](error_simulation.md) | Configured success and failure responses |

For realistic names, emails, companies, and cities, follow the complete [Capper walkthrough](../guides/realistic-data.md).

## Reading the outputs

The examples use fixed seeds where repeatability is useful. Exact generated values can change with dependency versions; linked values such as a requested name should keep matching the request. Fixed seeds can also repeat generated IDs, so use an ID returned by your running server when following a CRUD flow.

For an explicit failure followed by recovery, use [scenario steps](../guides/simulation-options.md#scenario-steps). Random error simulation is opt-in; normal routes default to `error_rate=0`.

## Verify the examples

Install test dependencies and run the documentation example runner from the repository root:

```bash
pip install -e ".[dev]"
python docs/guides/examples/run_examples.py
pytest tests/test_doc_examples.py -q
```

The runner prints real response data. The test checks that every registered example completes successfully.
