import time
from typing import Annotated, Any, TypedDict

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel, Field

from core import utils
from core.config import Config
from core.database.models import User
from core.database.models.user import find_user_by_id_and_tenant, find_user_for_login


settings = Config()
TOKEN_TTL_SECONDS = settings.backend_token_ttl_seconds
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    tenant: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class AuthenticatedUser(BaseModel):
    id: int
    username: str
    tenant: str
    tenant_id: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = TOKEN_TTL_SECONDS
    user: AuthenticatedUser


class AccessTokenClaims(TypedDict):
    sub: str
    tenant_id: int
    iat: int
    exp: int
    iss: str


def create_access_token(user: User) -> str:
    issued_at = int(time.time())
    claims: AccessTokenClaims = {
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "iat": issued_at,
        "exp": issued_at + TOKEN_TTL_SECONDS,
        "iss": settings.backend_token_issuer,
    }
    return jwt.encode(claims, settings.backend_token_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.backend_token_secret,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.backend_token_issuer,
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def _serialize_user(user: User) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        tenant=user.tenant.name,
        tenant_id=user.tenant_id,
    )


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not isinstance(user_id, str) or not isinstance(tenant_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        subject = int(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = await find_user_by_id_and_tenant(subject, tenant_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = await find_user_for_login(payload.username, payload.tenant)

    if user is None or not utils.password.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user)
    return LoginResponse(access_token=token, user=_serialize_user(user))


@router.get("/me", response_model=AuthenticatedUser)
async def me(user: Annotated[User, Depends(current_user)]) -> AuthenticatedUser:
    return _serialize_user(user)
