import time
from datetime import datetime
from typing import Annotated, TypedDict
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from backend.api.auth import JWT_ALGORITHM, current_user
from core.config import Config
from core.database.models import User
from core.database.models.scanner import (
    create_scanner,
    delete_scanner,
    find_scanner_for_tenant,
    list_scanners_for_tenant,
    update_scanner_name,
)


settings = Config()
SCANNER_TOKEN_TTL_SECONDS = settings.scanner_token_ttl_seconds
router = APIRouter(prefix="/scanners", tags=["scanners"])


class ScannerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ScannerUpdateRequest(BaseModel):
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
    jti: str


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
        "jti": str(uuid4()),
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


@router.patch("/{scanner_id}", response_model=ScannerResponse)
async def update(
    scanner_id: int,
    payload: ScannerUpdateRequest,
    user: Annotated[User, Depends(current_user)],
) -> ScannerResponse:
    scanner = await update_scanner_name(scanner_id, user.tenant_id, payload.name)
    if scanner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scanner not found")

    return _serialize_scanner(scanner)


@router.post("/{scanner_id}/token", response_model=ScannerCreateResponse)
async def reissue_token(
    scanner_id: int,
    user: Annotated[User, Depends(current_user)],
) -> ScannerCreateResponse:
    scanner = await find_scanner_for_tenant(scanner_id, user.tenant_id)
    if scanner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scanner not found")

    scanner_token = create_scanner_token(scanner.id, scanner.tenant_id)
    return ScannerCreateResponse(scanner=_serialize_scanner(scanner), scanner_token=scanner_token)


@router.delete("/{scanner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    scanner_id: int,
    user: Annotated[User, Depends(current_user)],
) -> Response:
    deleted = await delete_scanner(scanner_id, user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scanner not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
