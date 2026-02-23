"""
Phase 7 example: Request links — FromHeader, FromCookie.

Run: semblance run examples.request_links.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromCookie, FromHeader, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    """Query params for user endpoint."""

    name: str = "alice"


class UserResponse(BaseModel):
    """Response with request-bound fields."""

    name: Annotated[str, FromInput("name")]
    request_id: Annotated[str, FromHeader("X-Request-Id")]
    session: Annotated[str, FromCookie("session_id")]


api = SemblanceAPI(seed=42)


@api.get(
    "/user",
    input=UserQuery,
    output=UserResponse,
    summary="Get user (echoes header and cookie)",
)
def get_user():
    """request_id comes from X-Request-Id header; session from session_id cookie."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
