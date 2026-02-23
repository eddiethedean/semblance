# Concepts

A short overview of how Semblance works. Use this as a mental model and glossary; each topic links to the relevant guide.

## Input model

The **input model** is a Pydantic model that defines the shape of the request for an endpoint. For GET it usually describes query parameters (and path parameters if the route has `{id}` etc.). For POST, PUT, PATCH it describes the request body; path parameters are merged in. Field names and types determine validation and what your links can reference.

See [Input and Output Binding](input-output-binding.md).

## Output model

The **output model** is the Pydantic model that defines the response shape. It can be a single model or `list[Model]`. Semblance generates response instances from this model using Polyfactory; fields that have **links** get values from the request or from other output fields instead of random data.

See [Input and Output Binding](input-output-binding.md).

## Links

**Links** are metadata on output fields (via `Annotated[T, LinkType(...)]`) that tell Semblance where to get the value:

- **FromInput(field)** — Use the value of the named field from the input model.
- **DateRangeFrom(start, end)** — Generate a `datetime` between the two date fields on input.
- **WhenInput(cond_field, value, then_link)** — Apply the inner link only when the input field equals the given value.
- **ComputedFrom(fields, fn)** — Compute from other output fields (e.g. `full = first + " " + last`).
- **FromHeader(name)** / **FromCookie(name)** — Use the request header or cookie (Phase 7).

Custom link types can be registered with the plugin system.

See [Input and Output Binding](input-output-binding.md), [Advanced Links](advanced-links.md), [Request Links](request-links.md), [Plugins](plugins.md).

## list_count and filter_by

- **list_count** — For list endpoints, how many items to generate (fixed int or a field name on the input model).
- **filter_by** — Optional input field name; generated list items are filtered so that this field matches the input value (e.g. all items have `status=active` when the query has `status=active`).

See [Simulation Options](simulation-options.md).

## Seeding

- **seed** — `SemblanceAPI(seed=42)` makes random generation deterministic so the same inputs produce the same outputs (useful for tests).
- **seed_from** — Per-request seed from an input field so you can vary determinism per call.

See [Input and Output Binding](input-output-binding.md), [Testing](testing.md).

## Stateful store

When **stateful=True**, POST responses are stored in memory and GET list endpoints return stored items. Routes with a path param (e.g. `/users/{id}`) support GET by id (return stored or 404), PUT (upsert), PATCH (update), DELETE (remove). The store is keyed by **collection path** (e.g. `/users`); the first path param is the id field.

See [Stateful Mode](stateful-mode.md).

## Simulation options

Per-endpoint or global options that make the API behave more like a real service:

- **error_rate** / **error_codes** — Randomly return 4xx/5xx.
- **latency_ms** / **jitter_ms** — Simulate delay.
- **rate_limit** — Return 429 when too many requests per second.
- **validate_responses** — Validate generated responses against the output model (dev/CI).

See [Simulation Options](simulation-options.md).
