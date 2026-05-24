import json
from typing import Any

import nats
from fastapi import FastAPI
from nats.aio.client import Client as NATS

from core.config import Config
from core.database.models.scan_job import ScanJob, ScanJobStatus, update_scan_job_status


TENANT_SUBJECT_PREFIX = "opendiscovery.tenants"
SCAN_JOB_SUBJECT_TEMPLATE = TENANT_SUBJECT_PREFIX + ".{tenant_id}.scanners.{scanner_id}.jobs"
SCAN_JOB_STATUS_SUBJECT = TENANT_SUBJECT_PREFIX + ".*.scanners.*.jobs.*.status"

settings = Config()


def scan_job_subject(tenant_id: int, scanner_id: int) -> str:
    return SCAN_JOB_SUBJECT_TEMPLATE.format(tenant_id=tenant_id, scanner_id=scanner_id)


def scan_job_status_subject(tenant_id: int, scanner_id: int, scan_job_id: int) -> str:
    return f"{scan_job_subject(tenant_id, scanner_id)}.{scan_job_id}.status"


async def connect_nats(app: FastAPI) -> None:
    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_auth_user,
        password=settings.nats_auth_password,
        name="opendiscovery-backend",
    )
    app.state.nats = nc
    setattr(_get_nats, "_client", nc)
    await nc.subscribe(SCAN_JOB_STATUS_SUBJECT, cb=_handle_scan_job_status)
    await nc.flush()


async def disconnect_nats(app: FastAPI) -> None:
    nc: NATS | None = getattr(app.state, "nats", None)
    if nc is None:
        return
    await nc.drain()


def _scan_job_payload(scan_job: ScanJob) -> bytes:
    return json.dumps(
        {
            "id": scan_job.id,
            "ip_network": scan_job.ip_network,
            "tenant_id": scan_job.tenant_id,
            "scanner_id": scan_job.scanner_id,
            "status": scan_job.status.value,
            "created_at": scan_job.created_at.isoformat(),
        }
    ).encode()


async def publish_scan_job(scan_job: ScanJob) -> None:
    nc = await _get_nats()
    await nc.publish(scan_job_subject(scan_job.tenant_id, scan_job.scanner_id), _scan_job_payload(scan_job))
    await nc.flush()


async def _get_nats() -> NATS:
    nc = getattr(_get_nats, "_client", None)
    if nc is not None and not nc.is_closed:
        return nc

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_auth_user,
        password=settings.nats_auth_password,
        name="opendiscovery-backend-publisher",
    )
    setattr(_get_nats, "_client", nc)
    return nc


async def _handle_scan_job_status(msg) -> None:
    try:
        subject_tenant_id, subject_scanner_id, subject_scan_job_id = _parse_scan_job_status_subject(msg.subject)
        payload: dict[str, Any] = json.loads(msg.data.decode())
        scan_job_id = int(payload["id"])
        tenant_id = int(payload["tenant_id"])
        scanner_id = int(payload["scanner_id"])
        status = ScanJobStatus(payload["status"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return

    if (
        scan_job_id != subject_scan_job_id
        or tenant_id != subject_tenant_id
        or scanner_id != subject_scanner_id
    ):
        return

    await update_scan_job_status(scan_job_id, tenant_id, scanner_id, status)


def _parse_scan_job_status_subject(subject: str) -> tuple[int, int, int]:
    tokens = subject.split(".")
    if (
        len(tokens) != 8
        or tokens[0] != "opendiscovery"
        or tokens[1] != "tenants"
        or tokens[3] != "scanners"
        or tokens[5] != "jobs"
        or tokens[7] != "status"
    ):
        raise ValueError("invalid scan job status subject")

    return int(tokens[2]), int(tokens[4]), int(tokens[6])
