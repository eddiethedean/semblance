"""
Plugins example - custom link (FromEnv).

Run: semblance run examples.plugins.app:api --port 8000

Set USER_NAME env var to override the default:
  USER_NAME=Bob semblance run examples.plugins.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI, register_link


class FromEnv:
    """Custom link: read value from environment variable."""

    def __init__(self, env_var: str):
        self.env_var = env_var

    def resolve(self, input_data: dict, rng):
        import os
        return os.environ.get(self.env_var)


register_link(FromEnv)


class User(BaseModel):
    name: Annotated[str, FromEnv("USER_NAME")]
    role: Annotated[str, FromInput("role")]


class UserQuery(BaseModel):
    role: str = "viewer"


api = SemblanceAPI(seed=42)


@api.get(
    "/user",
    input=UserQuery,
    output=User,
    summary="Get user (name from USER_NAME env)",
)
def user():
    """name comes from USER_NAME env; role from query."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
