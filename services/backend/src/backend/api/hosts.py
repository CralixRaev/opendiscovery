from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from core.database.models import Host, Port, User
from core.database.models.asset import (
    count_hosts_for_tenant,
    list_hosts_for_tenant,
    list_open_ports_by_host_for_tenant,
)

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


class HostListResponse(BaseModel):
    items: list[HostResponse]
    total: int
    page: int
    page_size: int
    search: str
    sort_by: Literal["id", "ip", "created_at", "updated_at"]
    sort_direction: Literal["asc", "desc"]


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


@router.get("", response_model=HostListResponse)
async def list_hosts(
    user: Annotated[User, Depends(current_user)],
    search: Annotated[str, Query(max_length=128)] = "",
    sort_by: Literal["id", "ip", "created_at", "updated_at"] = "updated_at",
    sort_direction: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> HostListResponse:
    normalized_search = search.strip()
    offset = (page - 1) * page_size
    hosts = await list_hosts_for_tenant(
        user.tenant_id,
        search=normalized_search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=page_size,
        offset=offset,
    )
    total = await count_hosts_for_tenant(user.tenant_id, search=normalized_search)
    ports_by_host = await list_open_ports_by_host_for_tenant(
        user.tenant_id,
        [host.id for host in hosts],
    )

    return HostListResponse(
        items=[_serialize_host(host, ports_by_host.get(host.id, [])) for host in hosts],
        total=total,
        page=page,
        page_size=page_size,
        search=normalized_search,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
