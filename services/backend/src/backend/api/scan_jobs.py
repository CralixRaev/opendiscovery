from datetime import datetime
from ipaddress import ip_network
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.nats import publish_scan_job
from core.database.models import User
from core.database.models.scan_job import ScanJob, create_scan_job, list_scan_jobs_for_tenant

from .auth import current_user


router = APIRouter(prefix="/scan-jobs", tags=["scan-jobs"])


class ScanJobCreateRequest(BaseModel):
    ip_network: str = Field(min_length=1, max_length=128)
    scanner_id: int = Field(gt=0)

    @field_validator("ip_network")
    @classmethod
    def normalize_ip_network(cls, value: str) -> str:
        return str(ip_network(value, strict=False))


class ScanJobResponse(BaseModel):
    id: int
    ip_network: str
    created_at: datetime
    finished_at: datetime | None
    status: str
    tenant_id: int
    scanner_id: int


def _serialize_scan_job(scan_job: ScanJob) -> ScanJobResponse:
    return ScanJobResponse(
        id=scan_job.id,
        ip_network=scan_job.ip_network,
        created_at=scan_job.created_at,
        finished_at=scan_job.finished_at,
        status=scan_job.status.value,
        tenant_id=scan_job.tenant_id,
        scanner_id=scan_job.scanner_id,
    )


@router.get("", response_model=list[ScanJobResponse])
async def list_scan_jobs(user: Annotated[User, Depends(current_user)]) -> list[ScanJobResponse]:
    scan_jobs = await list_scan_jobs_for_tenant(user.tenant_id)
    return [_serialize_scan_job(scan_job) for scan_job in scan_jobs]


@router.post("", response_model=ScanJobResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ScanJobCreateRequest,
    user: Annotated[User, Depends(current_user)],
) -> ScanJobResponse:
    scan_job = await create_scan_job(payload.ip_network, user.tenant_id, payload.scanner_id)
    if scan_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scanner not found")

    await publish_scan_job(scan_job)
    return _serialize_scan_job(scan_job)
