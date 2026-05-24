from dataclasses import dataclass, field
from uuid import uuid4

from tortoise.transactions import in_transaction

from core.database.factories import (
    HostFactory,
    PortFactory,
    ScanJobFactory,
    ScannerFactory,
    TenantFactory,
    UserFactory,
)
from core.database.models.asset import Host, HostPort, Port
from core.database.models.discovery import (
    ScanJobHostDiscovery,
    ScanJobPortDiscovery,
    create_scan_job_host_discoveries,
    create_scan_job_port_discoveries,
)
from core.database.models.scan_job import ScanJob, create_scan_job
from core.database.models.scanner import Scanner, create_scanner
from core.database.models.tenant import Tenant, create_tenant
from core.database.models.user import User, create_user


@dataclass
class SeedDataSet:
    tenants: list[Tenant] = field(default_factory=list)
    users: list[User] = field(default_factory=list)
    scanners: list[Scanner] = field(default_factory=list)
    scan_jobs: list[ScanJob] = field(default_factory=list)
    hosts: list[Host] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)
    host_ports: list[HostPort] = field(default_factory=list)
    host_discoveries: list[ScanJobHostDiscovery] = field(default_factory=list)
    port_discoveries: list[ScanJobPortDiscovery] = field(default_factory=list)


async def populate_test_data(
    *,
    tenant_count: int = 2,
    users_per_tenant: int = 2,
    scanners_per_tenant: int = 2,
    scan_jobs_per_scanner: int = 2,
    hosts_per_scan_job: int = 3,
) -> SeedDataSet:
    data_set = SeedDataSet()
    seed_slug = uuid4().hex[:8]

    for tenant_index in range(tenant_count):
        tenant_draft = TenantFactory(name=f"demo-{seed_slug}-tenant-{tenant_index + 1}")
        async with in_transaction() as connection:
            tenant = await create_tenant(connection, tenant_draft.name)
        data_set.tenants.append(tenant)

        for user_index in range(users_per_tenant):
            password = "password"
            user_draft = UserFactory(
                username=f"demo-{seed_slug}-user-{tenant_index + 1}-{user_index + 1}",
                password=password,
                tenant=tenant,
            )
            async with in_transaction() as connection:
                user = await create_user(connection, user_draft.username, password, tenant)
            data_set.users.append(user)

        for scanner_index in range(scanners_per_tenant):
            scanner_draft = ScannerFactory(
                name=f"demo-{seed_slug}-scanner-{tenant_index + 1}-{scanner_index + 1}",
                tenant=tenant,
            )
            scanner = await create_scanner(scanner_draft.name, tenant)
            data_set.scanners.append(scanner)

            for scan_job_index in range(scan_jobs_per_scanner):
                scan_job_draft = ScanJobFactory(
                    ip_network=_scan_job_network(tenant_index, scanner_index, scan_job_index),
                    scanner=scanner,
                    tenant=tenant,
                )
                scan_job = await create_scan_job(
                    scan_job_draft.ip_network,
                    tenant.id,
                    scanner.id,
                )
                if scan_job is None:
                    continue
                data_set.scan_jobs.append(scan_job)

                host_ips = [
                    HostFactory(
                        ip=_host_ip(tenant_index, scanner_index, scan_job_index, host_index),
                        tenant=tenant,
                    ).ip
                    for host_index in range(hosts_per_scan_job)
                ]
                host_discoveries = await create_scan_job_host_discoveries(
                    scan_job.id,
                    tenant.id,
                    host_ips,
                )
                data_set.host_discoveries.extend(host_discoveries)
                data_set.hosts.extend([await discovery.host for discovery in host_discoveries])

                open_ports_by_ip = {
                    ip: [
                        _port_tuple(tenant_index, scanner_index, scan_job_index, host_index, port_index)
                        for port_index in range(2)
                    ]
                    for host_index, ip in enumerate(host_ips)
                }
                port_discoveries = await create_scan_job_port_discoveries(
                    scan_job.id,
                    tenant.id,
                    open_ports_by_ip,
                )
                data_set.port_discoveries.extend(port_discoveries)
                for discovery in port_discoveries:
                    host_port = await discovery.host_port
                    data_set.host_ports.append(host_port)
                    data_set.ports.append(await host_port.port)

    return data_set


def _scan_job_network(tenant_index: int, scanner_index: int, scan_job_index: int) -> str:
    return f"10.{tenant_index + 10}.{scanner_index * 16 + scan_job_index}.0/28"


def _host_ip(tenant_index: int, scanner_index: int, scan_job_index: int, host_index: int) -> str:
    return f"10.{tenant_index + 10}.{scanner_index * 16 + scan_job_index}.{host_index + 1}"


def _port_tuple(
    tenant_index: int,
    scanner_index: int,
    scan_job_index: int,
    host_index: int,
    port_index: int,
) -> tuple[int, str]:
    port_draft = PortFactory(
        number=_port_number(tenant_index, scanner_index, scan_job_index, host_index, port_index),
    )
    return port_draft.number, port_draft.service_name


def _port_number(
    tenant_index: int,
    scanner_index: int,
    scan_job_index: int,
    host_index: int,
    port_index: int,
) -> int:
    common_ports = [22, 80, 443, 5432, 8000]
    return common_ports[(tenant_index + scanner_index + scan_job_index + host_index + port_index) % len(common_ports)]
