from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.database.models import Host, User
from core.database.models.asset import list_hosts_for_tenant

from .auth import current_user


router = APIRouter(prefix="/hosts", tags=["hosts"])


class HostResponse(BaseModel):
    id: int
    ip: str
    created_at: datetime
    updated_at: datetime
    tenant_id: int


def _serialize_host(host: Host) -> HostResponse:
    return HostResponse(
        id=host.id,
        ip=str(host.ip),
        created_at=host.created_at,
        updated_at=host.updated_at,
        tenant_id=host.tenant_id,
    )


@router.get("", response_model=list[HostResponse])
async def list_hosts(user: Annotated[User, Depends(current_user)]) -> list[HostResponse]:
    hosts = await list_hosts_for_tenant(user.tenant_id)
    return [_serialize_host(host) for host in hosts]
