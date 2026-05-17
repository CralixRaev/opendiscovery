from tortoise import Model, fields

from core.database import mark_from_db, use_raw_queries
from core.database.fields import InetField


class Host(Model):
    ip = InetField(null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='hosts')

    def __str__(self) -> str:
        return self.ip


class Port(Model):
    number = fields.IntField(null=False)
    service_name = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='ports')

    def __str__(self) -> str:
        return f'{self.number}/{self.service_name}'


class HostPort(Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='host_ports')
    host = fields.ForeignKeyField('models.Host', related_name='host_ports')
    port = fields.ForeignKeyField('models.Port', related_name='host_ports')

    def __str__(self) -> str:
        return f'{self.host_id}:{self.port_id}'


async def get_or_create_host(tenant_id: int, ip: str) -> Host:
    if use_raw_queries():
        connection = Host._meta.db
        rows = await connection.execute_query_dict(
            (
                'WITH existing AS ('
                '    SELECT "id", "ip", "created_at", "updated_at", "tenant_id" '
                '    FROM "host" '
                '    WHERE "tenant_id" = $1 AND "ip" = $2::inet '
                '    LIMIT 1'
                '), inserted AS ('
                '    INSERT INTO "host" ("ip", "created_at", "updated_at", "tenant_id") '
                '    SELECT $2::inet, NOW(), NOW(), $1 '
                '    WHERE NOT EXISTS (SELECT 1 FROM existing) '
                '    RETURNING "id", "ip", "created_at", "updated_at", "tenant_id"'
                ') '
                'SELECT "id", "ip", "created_at", "updated_at", "tenant_id" FROM existing '
                'UNION ALL '
                'SELECT "id", "ip", "created_at", "updated_at", "tenant_id" FROM inserted '
                'LIMIT 1'
            ),
            [tenant_id, ip],
        )
        return _host_from_row(rows[0])

    host = await Host.get_or_none(tenant_id=tenant_id, ip=ip)
    if host is not None:
        return host

    host = Host(tenant_id=tenant_id, ip=ip)
    await host.save()
    return host


async def get_or_create_port(tenant_id: int, number: int, service_name: str) -> Port:
    if use_raw_queries():
        connection = Port._meta.db
        rows = await connection.execute_query_dict(
            (
                'WITH existing AS ('
                '    SELECT "id", "number", "service_name", "created_at", "updated_at", "tenant_id" '
                '    FROM "port" '
                '    WHERE "tenant_id" = $1 AND "number" = $2 AND "service_name" = $3 '
                '    LIMIT 1'
                '), inserted AS ('
                '    INSERT INTO "port" ("number", "service_name", "created_at", "updated_at", "tenant_id") '
                '    SELECT $2, $3, NOW(), NOW(), $1 '
                '    WHERE NOT EXISTS (SELECT 1 FROM existing) '
                '    RETURNING "id", "number", "service_name", "created_at", "updated_at", "tenant_id"'
                ') '
                'SELECT "id", "number", "service_name", "created_at", "updated_at", "tenant_id" FROM existing '
                'UNION ALL '
                'SELECT "id", "number", "service_name", "created_at", "updated_at", "tenant_id" FROM inserted '
                'LIMIT 1'
            ),
            [tenant_id, number, service_name],
        )
        return _port_from_row(rows[0])

    port = await Port.get_or_none(
        tenant_id=tenant_id,
        number=number,
        service_name=service_name,
    )
    if port is not None:
        return port

    port = Port(tenant_id=tenant_id, number=number, service_name=service_name)
    await port.save()
    return port


async def get_or_create_host_port(tenant_id: int, host_id: int, port_id: int) -> HostPort:
    if use_raw_queries():
        connection = HostPort._meta.db
        rows = await connection.execute_query_dict(
            (
                'WITH existing AS ('
                '    SELECT "id", "created_at", "updated_at", "tenant_id", "host_id", "port_id" '
                '    FROM "hostport" '
                '    WHERE "tenant_id" = $1 AND "host_id" = $2 AND "port_id" = $3 '
                '    LIMIT 1'
                '), inserted AS ('
                '    INSERT INTO "hostport" ("created_at", "updated_at", "tenant_id", "host_id", "port_id") '
                '    SELECT NOW(), NOW(), $1, $2, $3 '
                '    WHERE NOT EXISTS (SELECT 1 FROM existing) '
                '    RETURNING "id", "created_at", "updated_at", "tenant_id", "host_id", "port_id"'
                ') '
                'SELECT "id", "created_at", "updated_at", "tenant_id", "host_id", "port_id" FROM existing '
                'UNION ALL '
                'SELECT "id", "created_at", "updated_at", "tenant_id", "host_id", "port_id" FROM inserted '
                'LIMIT 1'
            ),
            [tenant_id, host_id, port_id],
        )
        return _host_port_from_row(rows[0])

    host_port = await HostPort.get_or_none(
        tenant_id=tenant_id,
        host_id=host_id,
        port_id=port_id,
    )
    if host_port is not None:
        return host_port

    host_port = HostPort(tenant_id=tenant_id, host_id=host_id, port_id=port_id)
    await host_port.save()
    return host_port


async def list_hosts_for_tenant(tenant_id: int) -> list[Host]:
    if use_raw_queries():
        connection = Host._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT "id", "ip", "created_at", "updated_at", "tenant_id" '
                'FROM "host" '
                'WHERE "tenant_id" = $1 '
                'ORDER BY "updated_at" DESC, "id" DESC'
            ),
            [tenant_id],
        )
        return [_host_from_row(row) for row in rows]

    return await Host.filter(tenant_id=tenant_id).order_by("-updated_at", "-id")


async def list_open_ports_by_host_for_tenant(tenant_id: int) -> dict[int, list[Port]]:
    if use_raw_queries():
        connection = HostPort._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT '
                '    hp."host_id", p."id", p."number", p."service_name", '
                '    p."created_at", p."updated_at", p."tenant_id" '
                'FROM "hostport" hp '
                'JOIN "port" p ON p."id" = hp."port_id" '
                'WHERE hp."tenant_id" = $1 '
                'ORDER BY hp."host_id", p."number", p."service_name"'
            ),
            [tenant_id],
        )
    else:
        rows = await HostPort.filter(tenant_id=tenant_id).select_related("port").order_by(
            "host_id",
            "port__number",
            "port__service_name",
        )
        ports_by_host: dict[int, list[Port]] = {}
        for host_port in rows:
            ports_by_host.setdefault(host_port.host_id, []).append(host_port.port)
        return ports_by_host

    ports_by_host: dict[int, list[Port]] = {}
    for row in rows:
        ports_by_host.setdefault(row["host_id"], []).append(_port_from_row(row))
    return ports_by_host


def _host_from_row(row: dict) -> Host:
    return mark_from_db(
        Host(
            id=row['id'],
            ip=str(row['ip']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            tenant_id=row['tenant_id'],
        )
    )


def _port_from_row(row: dict) -> Port:
    return mark_from_db(
        Port(
            id=row['id'],
            number=row['number'],
            service_name=row['service_name'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            tenant_id=row['tenant_id'],
        )
    )


def _host_port_from_row(row: dict) -> HostPort:
    return mark_from_db(
        HostPort(
            id=row['id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            tenant_id=row['tenant_id'],
            host_id=row['host_id'],
            port_id=row['port_id'],
        )
    )
