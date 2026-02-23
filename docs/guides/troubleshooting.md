# Troubleshooting

Common issues and how to fix them.

## 404 on stateful GET / PATCH / DELETE by id

**Symptom:** Request to e.g. `GET /users/abc` returns 404 when you expected a stored item.

**Causes:**

- The id is not in the store (no POST or PUT created it, or the store was cleared).
- The path param name must match what Semblance uses for the store: the first path parameter (e.g. `{id}`) is the id field. The collection path is derived by stripping the last `/{param}` segment (e.g. `/users/{id}` → `/users`).

**Fix:** Ensure you create the resource first (POST or PUT), or call the correct id. Use `SemblanceAPI(verbose_errors=True)` to get 404 responses that include `collection`, `id_field`, and `id_value` for debugging.

See [Stateful Mode](stateful-mode.md).

## 422 validation errors

**Symptom:** The API returns 422 with a validation error body.

**Cause:** Query parameters, request body, or path parameters don’t match the endpoint’s **input model** (types, required fields, or field names).

**Fix:** Check the input model for that route and send the expected shape. Use the OpenAPI schema (`/openapi.json` or `semblance export openapi app:api`) to see the exact contract.

See [Input and Output Binding](input-output-binding.md).

## 429 in tests

**Symptom:** Requests return 429 (rate limit exceeded) during tests.

**Cause:** The endpoint has `rate_limit=N` and the test sends more than N requests per second (sliding window).

**Fix:** Disable rate limiting for that endpoint (`rate_limit=None`), use a higher value, or space out requests. Use a fixed `seed` for deterministic responses when you don’t care about rate-limit behavior in the test.

See [Simulation Options](simulation-options.md).

## Response doesn’t match query (e.g. wrong name)

**Symptom:** You pass `?name=alice` but the response has a different or generated name.

**Cause:** The output field is bound with `FromInput("name")` but the name doesn’t match a field on the **input model** for that endpoint (e.g. a typo like `FromInput("nam")`), or the input model doesn’t have that field.

**Fix:** Ensure the link’s field name exactly matches a field on the input model. Enable `SemblanceAPI(validate_links=True)` to get startup errors for invalid link bindings, or run `semblance validate app:api`.

See [Input and Output Binding](input-output-binding.md).

## Duplicate endpoint error

**Symptom:** `ValueError: Duplicate METHOD endpoint registered for path '...'` when building the app.

**Cause:** The same (path, method) is registered more than once (e.g. two `@api.get("/users")` handlers).

**Fix:** Register only one handler per (path, method). Remove or merge the duplicate decorator.

## Module / attr not found

**Symptom:** `semblance run app:api` or `semblance validate app:api` fails with “Module … not found” or “Attribute … not found”.

**Causes:**

- The working directory or `PYTHONPATH` doesn’t allow importing the module (e.g. run from the project root, or set `PYTHONPATH`).
- The module:attr is wrong (e.g. the variable is named `api` but you passed `app`).

**Fix:** Run from the directory that contains the package/module, or add it to `PYTHONPATH`. Use `module:attr` (e.g. `app:api` or `app:app`). If you pass only the module and there’s a single SemblanceAPI or FastAPI in it, the CLI infers the attr.

See [CLI](cli.md).
