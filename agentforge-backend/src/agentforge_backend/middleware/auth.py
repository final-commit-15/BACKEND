from fastapi import Request, HTTPException, status
from ..security.jwt import decode_token
from ..utils.exceptions import AuthenticationError

async def get_current_user_id(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid token")
    token = auth.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise AuthenticationError("Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    return user_id