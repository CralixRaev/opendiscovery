from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any


class InvalidScanJobResultError(ValueError):
    pass


@dataclass(frozen=True)
class AliveHostResult:
    ip: str
    hostname: str | None = None


@dataclass(frozen=True)
class ScanJobResult:
    id: int
    tenant_id: int
    scanner_id: int
    ip_network: str
    alive_hosts: list[AliveHostResult]


def parse_scan_job_result(payload: dict[str, Any]) -> ScanJobResult:
    try:
        alive_hosts_payload = payload["alive_hosts"]
        if not isinstance(alive_hosts_payload, list):
            raise InvalidScanJobResultError("alive_hosts must be a list")

        return ScanJobResult(
            id=int(payload["id"]),
            tenant_id=int(payload["tenant_id"]),
            scanner_id=int(payload["scanner_id"]),
            ip_network=str(payload["ip_network"]),
            alive_hosts=[parse_alive_host(host) for host in alive_hosts_payload],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidScanJobResultError("invalid scan job result payload") from exc


def parse_scan_job_result_subject(subject: str) -> tuple[int, int, int]:
    tokens = subject.split(".")
    if (
        len(tokens) != 8
        or tokens[0] != "opendiscovery"
        or tokens[1] != "tenants"
        or tokens[3] != "scanners"
        or tokens[5] != "jobs"
        or tokens[7] != "result"
    ):
        raise InvalidScanJobResultError("invalid scan job result subject")

    return int(tokens[2]), int(tokens[4]), int(tokens[6])


def parse_alive_host(payload: Any) -> AliveHostResult:
    if not isinstance(payload, dict):
        raise InvalidScanJobResultError("alive host must be an object")

    ip = str(payload["ip"])
    ip_address(ip)

    hostname = payload.get("hostname")
    if hostname is not None:
        hostname = str(hostname)

    return AliveHostResult(ip=ip, hostname=hostname)
