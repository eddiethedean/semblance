"""
Error simulation example - error_rate, error_codes.

Run: semblance run examples.error_simulation.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


class UserQuery(BaseModel):
    name: str = "alice"


api = SemblanceAPI(seed=99)


@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
    list_count=2,
    error_rate=0.3,
    error_codes=[404, 503],
    summary="List users (may fail randomly)",
)
def users():
    """30% of requests return 404 or 503. Use error_rate=0 for tests."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
