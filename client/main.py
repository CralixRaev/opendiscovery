import asyncio
import json

import nats
from nats.errors import Error

from config import ClientConfig
from nmap_scan import NmapScanError, NmapScanResult, scan_alive_hosts


async def publish_status(nc, config: ClientConfig, scan_job: dict, status: str) -> None:
    payload = {
        "id": scan_job["id"],
        "tenant_id": scan_job["tenant_id"],
        "scanner_id": scan_job["scanner_id"],
        "status": status,
    }
    await nc.publish(config.scan_job_status_subject(scan_job["id"]), json.dumps(payload).encode())
    await nc.flush()


async def publish_result(nc, config: ClientConfig, scan_job: dict, result: NmapScanResult) -> None:
    payload = {
        "id": scan_job["id"],
        "tenant_id": scan_job["tenant_id"],
        "scanner_id": scan_job["scanner_id"],
        "ip_network": result.target,
        "alive_hosts": [
            {
                "ip": host.ip,
                "hostname": host.hostname,
            }
            for host in result.alive_hosts
        ],
    }
    await nc.publish(config.scan_job_result_subject(scan_job["id"]), json.dumps(payload).encode())
    await nc.flush()


async def process_scan_job(nc, config: ClientConfig, msg) -> None:
    try:
        scan_job = json.loads(msg.data.decode())
    except json.JSONDecodeError:
        print("received invalid scan job payload")
        return

    if not {"id", "ip_network", "tenant_id", "scanner_id"}.issubset(scan_job):
        print("received incomplete scan job payload")
        return

    print(f"received scan job #{scan_job['id']} for {scan_job['ip_network']}")

    await publish_status(nc, config, scan_job, "running")
    print(f"scan job #{scan_job['id']} is running")

    try:
        scan_result = await scan_alive_hosts(scan_job["ip_network"])
    except (ValueError, NmapScanError) as exc:
        await publish_status(nc, config, scan_job, "failed")
        print(f"scan job #{scan_job['id']} failed: {exc}")
        return

    await publish_result(nc, config, scan_job, scan_result)
    await publish_status(nc, config, scan_job, "finished")
    print(
        f"scan job #{scan_job['id']} is finished: "
        f"{len(scan_result.alive_hosts)} alive host(s) found"
    )


async def run() -> None:
    config = ClientConfig()
    nc = await nats.connect(
        config.nats_url,
        token=config.scanner_token,
        name=config.client_name,
        allow_reconnect=False,
    )

    subject = config.subject

    async def handle_message(msg) -> None:
        await process_scan_job(nc, config, msg)

    await nc.subscribe(subject, cb=handle_message)
    await nc.flush()

    print(f"scanner client is listening on {subject}")
    await asyncio.Event().wait()


def main() -> None:
    try:
        asyncio.run(run())
    except Error as exc:
        raise SystemExit(f"NATS connection failed: {exc}") from exc


if __name__ == "__main__":
    main()
