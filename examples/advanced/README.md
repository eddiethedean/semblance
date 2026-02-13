# Advanced Example

WhenInput, ComputedFrom, and filter_by.

## Run

```bash
semblance run examples.advanced.app:api --port 8000
```

## Try

```bash
# WhenInput - status applied only when include_status=true
curl "http://127.0.0.1:8000/user/status?name=alice&include_status=true&status=active"

# ComputedFrom - full name computed from first + last
curl "http://127.0.0.1:8000/user/fullname?first=Jane&last=Smith"

# filter_by - all list items match status
curl "http://127.0.0.1:8000/users?name=x&status=active"
```

## Concepts

- **WhenInput(cond, val, link)** – apply link only when cond matches
- **ComputedFrom(fields, fn)** – compute field from other output fields
- **filter_by** – filter list items to those matching input field value
