from tortoise import Model, fields

from core.database import mark_from_db, use_raw_queries
from core.database.models.asset import get_or_create_host, get_or_create_host_port, get_or_create_port
from core.database.models.scan_job import find_scan_job_for_scanner


class ScanJobHostDiscovery(Model):
    tenant = fields.ForeignKeyField(
        'models.Tenant',
        related_name='scan_job_host_discoveries',
    )
    scan_job = fields.ForeignKeyField('models.ScanJob', related_name='host_discoveries')
    host = fields.ForeignKeyField('models.Host', related_name='scan_job_discoveries')


class ScanJobPortDiscovery(Model):
    tenant = fields.ForeignKeyField(
        'models.Tenant',
        related_name='scan_job_port_discoveries',
    )
    scan_job = fields.ForeignKeyField('models.ScanJob', related_name='port_discoveries')
    host_port = fields.ForeignKeyField(
        'models.HostPort',
        related_name='scan_job_discoveries',
    )


async def create_scan_job_host_discoveries(
    scan_job_id: int,
    tenant_id: int,
    ips: list[str],
) -> list[ScanJobHostDiscovery]:
    discoveries: list[ScanJobHostDiscovery] = []
    for ip in ips:
        host = await get_or_create_host(tenant_id, ip)
        discoveries.append(await get_or_create_scan_job_host_discovery(tenant_id, scan_job_id, host.id))
    return discoveries


async def create_scan_job_host_discoveries_for_scanner(
    scan_job_id: int,
    tenant_id: int,
    scanner_id: int,
    ips: list[str],
) -> list[ScanJobHostDiscovery]:
    scan_job = await find_scan_job_for_scanner(scan_job_id, tenant_id, scanner_id)
    if scan_job is None:
        return []

    return await create_scan_job_host_discoveries(scan_job.id, tenant_id, ips)


async def create_scan_job_port_discoveries(
    scan_job_id: int,
    tenant_id: int,
    open_ports_by_ip: dict[str, list[tuple[int, str]]],
) -> list[ScanJobPortDiscovery]:
    discoveries: list[ScanJobPortDiscovery] = []
    for ip, open_ports in open_ports_by_ip.items():
        host = await get_or_create_host(tenant_id, ip)
        for port_number, service_name in open_ports:
            port = await get_or_create_port(tenant_id, port_number, service_name)
            host_port = await get_or_create_host_port(tenant_id, host.id, port.id)
            discoveries.append(
                await get_or_create_scan_job_port_discovery(tenant_id, scan_job_id, host_port.id)
            )
    return discoveries


async def create_scan_job_port_discoveries_for_scanner(
    scan_job_id: int,
    tenant_id: int,
    scanner_id: int,
    open_ports_by_ip: dict[str, list[tuple[int, str]]],
) -> list[ScanJobPortDiscovery]:
    scan_job = await find_scan_job_for_scanner(scan_job_id, tenant_id, scanner_id)
    if scan_job is None:
        return []

    return await create_scan_job_port_discoveries(scan_job.id, tenant_id, open_ports_by_ip)


async def get_or_create_scan_job_host_discovery(
    tenant_id: int,
    scan_job_id: int,
    host_id: int,
) -> ScanJobHostDiscovery:
    if use_raw_queries():
        connection = ScanJobHostDiscovery._meta.db
        rows = await connection.execute_query_dict(
            (
                'WITH existing AS ('
                '    SELECT "id", "tenant_id", "scan_job_id", "host_id" '
                '    FROM "scanjobhostdiscovery" '
                '    WHERE "tenant_id" = $1 AND "scan_job_id" = $2 AND "host_id" = $3 '
                '    LIMIT 1'
                '), inserted AS ('
                '    INSERT INTO "scanjobhostdiscovery" ("tenant_id", "scan_job_id", "host_id") '
                '    SELECT $1, $2, $3 '
                '    WHERE NOT EXISTS (SELECT 1 FROM existing) '
                '    RETURNING "id", "tenant_id", "scan_job_id", "host_id"'
                ') '
                'SELECT "id", "tenant_id", "scan_job_id", "host_id" FROM existing '
                'UNION ALL '
                'SELECT "id", "tenant_id", "scan_job_id", "host_id" FROM inserted '
                'LIMIT 1'
            ),
            [tenant_id, scan_job_id, host_id],
        )
        return _scan_job_host_discovery_from_row(rows[0])

    discovery = await ScanJobHostDiscovery.get_or_none(
        tenant_id=tenant_id,
        scan_job_id=scan_job_id,
        host_id=host_id,
    )
    if discovery is not None:
        return discovery

    discovery = ScanJobHostDiscovery(
        tenant_id=tenant_id,
        scan_job_id=scan_job_id,
        host_id=host_id,
    )
    await discovery.save()
    return discovery


async def get_or_create_scan_job_port_discovery(
    tenant_id: int,
    scan_job_id: int,
    host_port_id: int,
) -> ScanJobPortDiscovery:
    if use_raw_queries():
        connection = ScanJobPortDiscovery._meta.db
        rows = await connection.execute_query_dict(
            (
                'WITH existing AS ('
                '    SELECT "id", "tenant_id", "scan_job_id", "host_port_id" '
                '    FROM "scanjobportdiscovery" '
                '    WHERE "tenant_id" = $1 AND "scan_job_id" = $2 AND "host_port_id" = $3 '
                '    LIMIT 1'
                '), inserted AS ('
                '    INSERT INTO "scanjobportdiscovery" ("tenant_id", "scan_job_id", "host_port_id") '
                '    SELECT $1, $2, $3 '
                '    WHERE NOT EXISTS (SELECT 1 FROM existing) '
                '    RETURNING "id", "tenant_id", "scan_job_id", "host_port_id"'
                ') '
                'SELECT "id", "tenant_id", "scan_job_id", "host_port_id" FROM existing '
                'UNION ALL '
                'SELECT "id", "tenant_id", "scan_job_id", "host_port_id" FROM inserted '
                'LIMIT 1'
            ),
            [tenant_id, scan_job_id, host_port_id],
        )
        return _scan_job_port_discovery_from_row(rows[0])

    discovery = await ScanJobPortDiscovery.get_or_none(
        tenant_id=tenant_id,
        scan_job_id=scan_job_id,
        host_port_id=host_port_id,
    )
    if discovery is not None:
        return discovery

    discovery = ScanJobPortDiscovery(
        tenant_id=tenant_id,
        scan_job_id=scan_job_id,
        host_port_id=host_port_id,
    )
    await discovery.save()
    return discovery


def _scan_job_host_discovery_from_row(row: dict) -> ScanJobHostDiscovery:
    return mark_from_db(
        ScanJobHostDiscovery(
            id=row['id'],
            tenant_id=row['tenant_id'],
            scan_job_id=row['scan_job_id'],
            host_id=row['host_id'],
        )
    )


def _scan_job_port_discovery_from_row(row: dict) -> ScanJobPortDiscovery:
    return mark_from_db(
        ScanJobPortDiscovery(
            id=row['id'],
            tenant_id=row['tenant_id'],
            scan_job_id=row['scan_job_id'],
            host_port_id=row['host_port_id'],
        )
    )
