# Plugins

Register custom link types to extend Semblance's binding behavior.

## Register a Link

Implement a class with a `resolve(input_data: dict, rng)` method and register it:

```python
from semblance import register_link, SemblanceAPI

class FromEnv:
    def __init__(self, env_var: str):
        self.env_var = env_var

    def resolve(self, input_data: dict, rng) -> str | None:
        import os
        return os.environ.get(self.env_var)

register_link(FromEnv)
```

Then use it in output models:

```python
from typing import Annotated
from pydantic import BaseModel

class User(BaseModel):
    name: Annotated[str, FromEnv("USER_NAME")]
```

## Resolve Signature

- `input_data` – validated input as a dict (from `model_dump()`)
- `rng` – `random.Random` instance (seeded when `SemblanceAPI(seed=...)` or `seed_from` is used)
- Return value is used as the field value; return `None` to let Polyfactory generate

## Example: RandomChoice

Pick a value from an input list:

```python
class RandomChoice:
    def __init__(self, field: str):
        self.field = field

    def resolve(self, input_data: dict, rng) -> str | None:
        opts = input_data.get(self.field)
        if opts and isinstance(opts, (list, tuple)):
            return rng.choice(opts)
        return None

register_link(RandomChoice)

class Item(BaseModel):
    choice: Annotated[str, RandomChoice("options")]

class QueryWithOptions(BaseModel):
    options: list[str] = ["a", "b", "c"]
```

**Example output (`GET /item?options=a&options=b&options=c` with seed=42):**

```json
{"choice": "c"}
```

## Check Registration

```python
from semblance.plugins import get_registered_links, is_registered

register_link(FromEnv)
assert FromEnv in get_registered_links()
assert is_registered(FromEnv("X"))
```
