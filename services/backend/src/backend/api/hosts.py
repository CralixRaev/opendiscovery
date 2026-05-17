from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.database.models import Host, Port, User
from core.database.models.asset import list_hosts_for_tenant, list_open_ports_by_host_for_tenant

from .auth import current_user


router = APIRouter(prefix="/hosts", tags=["hosts"])


class OpenPortResponse(BaseModel):
    number: int
    service_name: str


class HostResponse(BaseModel):
    id: int
    ip: str
    created_at: datetime
    updated_at: datetime
    tenant_id: int
    open_ports: list[OpenPortResponse]


def _serialize_port(port: Port) -> OpenPortResponse:
    return OpenPortResponse(number=port.number, service_name=port.service_name)


def _serialize_host(host: Host, open_ports: list[Port]) -> HostResponse:
    return HostResponse(
        id=host.id,
        ip=str(host.ip),
        created_at=host.created_at,
        updated_at=host.updated_at,
        tenant_id=host.tenant_id,
        open_ports=[_serialize_port(port) for port in open_ports],
    )


@router.get("", response_model=list[HostResponse])
async def list_hosts(user: Annotated[User, Depends(current_user)]) -> list[HostResponse]:
    hosts = await list_hosts_for_tenant(user.tenant_id)
    ports_by_host = await list_open_ports_by_host_for_tenant(user.tenant_id)
    return [_serialize_host(host, ports_by_host.get(host.id, [])) for host in hosts]
