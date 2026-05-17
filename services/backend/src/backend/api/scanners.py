import time
from datetime import datetime
from typing import Annotated, TypedDict

import jwt
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.auth import JWT_ALGORITHM, current_user
from core.config import Config
from core.database.models import User
from core.database.models.scanner import create_scanner, list_scanners_for_tenant


settings = Config()
SCANNER_TOKEN_TTL_SECONDS = settings.backend_token_ttl_seconds
router = APIRouter(prefix="/scanners", tags=["scanners"])


class ScannerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ScannerResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    tenant_id: int


class ScannerCreateResponse(BaseModel):
    scanner: ScannerResponse
    scanner_token: str
    token_type: str = "bearer"
    expires_in: int = SCANNER_TOKEN_TTL_SECONDS


class ScannerTokenClaims(TypedDict):
    sub: str
    scanner_id: int
    tenant_id: int
    iat: int
    exp: int
    iss: str
    token_use: str


def create_scanner_token(scanner_id: int, tenant_id: int) -> str:
    issued_at = int(time.time())
    claims: ScannerTokenClaims = {
        "sub": str(scanner_id),
        "scanner_id": scanner_id,
        "tenant_id": tenant_id,
        "iat": issued_at,
        "exp": issued_at + SCANNER_TOKEN_TTL_SECONDS,
        "iss": settings.backend_token_issuer,
        "token_use": "scanner",
    }
    return jwt.encode(claims, settings.backend_token_secret, algorithm=JWT_ALGORITHM)


def _serialize_scanner(scanner) -> ScannerResponse:
    return ScannerResponse(
        id=scanner.id,
        name=scanner.name,
        created_at=scanner.created_at,
        tenant_id=scanner.tenant_id,
    )


@router.get("", response_model=list[ScannerResponse])
async def list_scanners(user: Annotated[User, Depends(current_user)]) -> list[ScannerResponse]:
    scanners = await list_scanners_for_tenant(user.tenant_id)
    return [_serialize_scanner(scanner) for scanner in scanners]


@router.post("", response_model=ScannerCreateResponse)
async def create(
    payload: ScannerCreateRequest,
    user: Annotated[User, Depends(current_user)],
) -> ScannerCreateResponse:
    scanner = await create_scanner(payload.name, user.tenant)
    scanner_token = create_scanner_token(scanner.id, scanner.tenant_id)
    return ScannerCreateResponse(scanner=_serialize_scanner(scanner), scanner_token=scanner_token)
