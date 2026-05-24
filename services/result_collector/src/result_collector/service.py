import asyncio
import json
import signal
from typing import Any

import nats
from core.config import Config
from core.database import build_tortoise_config
from core.database.models.discovery import (
    create_scan_job_host_discoveries_for_scanner,
    create_scan_job_port_discoveries_for_scanner,
)
from tortoise import Tortoise

from result_collector.payloads import (
    InvalidScanJobResultError,
    parse_scan_job_result,
    parse_scan_job_result_subject,
)


TENANT_SUBJECT_PREFIX = "opendiscovery.tenants"
SCAN_JOB_RESULT_SUBJECT = TENANT_SUBJECT_PREFIX + ".*.scanners.*.jobs.*.result"
SCAN_JOB_RESULT_QUEUE = "opendiscovery-result-collectors"


async def run() -> None:
    settings = Config()
    await Tortoise.init(
        config=build_tortoise_config(),
        _enable_global_fallback=True,
    )

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_auth_user,
        password=settings.nats_auth_password,
        name="opendiscovery-result-collector",
    )

    async def handle_scan_job_result(msg) -> None:
        await process_scan_job_result_message(msg.subject, msg.data)

    await nc.subscribe(SCAN_JOB_RESULT_SUBJECT, queue=SCAN_JOB_RESULT_QUEUE, cb=handle_scan_job_result)
    await nc.flush()
    print(f"result collector is listening on {SCAN_JOB_RESULT_SUBJECT}")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    try:
        await stop.wait()
    finally:
        try:
            await nc.drain()
        except Exception:
            await nc.close()
        await Tortoise.close_connections()


async def process_scan_job_result_message(subject: str, data: bytes) -> None:
    try:
        subject_tenant_id, subject_scanner_id, subject_scan_job_id = parse_scan_job_result_subject(subject)
        payload: dict[str, Any] = json.loads(data.decode())
        result = parse_scan_job_result(payload)
    except (InvalidScanJobResultError, ValueError, json.JSONDecodeError):
        return

    if (
        result.id != subject_scan_job_id
        or result.tenant_id != subject_tenant_id
        or result.scanner_id != subject_scanner_id
    ):
        return

    await create_scan_job_host_discoveries_for_scanner(
        scan_job_id=result.id,
        tenant_id=result.tenant_id,
        scanner_id=result.scanner_id,
        ips=[host.ip for host in result.alive_hosts],
    )
    await create_scan_job_port_discoveries_for_scanner(
        scan_job_id=result.id,
        tenant_id=result.tenant_id,
        scanner_id=result.scanner_id,
        open_ports_by_ip={
            host.ip: [(port.number, port.service_name) for port in host.open_ports or []]
            for host in result.alive_hosts
        },
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
