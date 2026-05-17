from typing import Literal

from tortoise import Model, fields
from tortoise.expressions import Q

from core.database import get_read_connection, mark_from_db, use_raw_queries, using_read_connection
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


HostSortBy = Literal["id", "ip", "created_at", "updated_at"]
SortDirection = Literal["asc", "desc"]

_HOST_SORT_COLUMNS: dict[HostSortBy, str] = {
    "id": '"id"',
    "ip": '"ip"',
    "created_at": '"created_at"',
    "updated_at": '"updated_at"',
}


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


def _host_search_condition(search: str) -> Q:
    condition = Q(ip__icontains=search) | Q(host_ports__port__service_name__icontains=search)
    if search.isdigit():
        value = int(search)
        condition |= Q(id=value) | Q(host_ports__port__number=value)
    return condition


async def list_hosts_for_tenant(
    tenant_id: int,
    *,
    search: str = "",
    sort_by: HostSortBy = "updated_at",
    sort_direction: SortDirection = "desc",
    limit: int | None = None,
    offset: int = 0,
) -> list[Host]:
    search = search.strip()
    if use_raw_queries():
        connection = get_read_connection()
        order_column = _HOST_SORT_COLUMNS[sort_by]
        order_direction = "ASC" if sort_direction == "asc" else "DESC"
        pagination_sql = ""
        params: list[object] = [tenant_id, search, f"%{search}%"]
        if limit is not None:
            pagination_sql = 'LIMIT $4 OFFSET $5'
            params.extend([limit, offset])
        rows = await connection.execute_query_dict(
            (
                'SELECT h."id", h."ip", h."created_at", h."updated_at", h."tenant_id" '
                'FROM "host" h '
                'WHERE h."tenant_id" = $1 '
                'AND ('
                '    $2 = \'\' '
                '    OR h."ip"::text ILIKE $3 '
                '    OR h."id"::text = $2 '
                '    OR EXISTS ('
                '        SELECT 1 '
                '        FROM "hostport" hp '
                '        JOIN "port" p ON p."id" = hp."port_id" '
                '        WHERE hp."host_id" = h."id" '
                '        AND hp."tenant_id" = h."tenant_id" '
                '        AND (p."service_name" ILIKE $3 OR p."number"::text ILIKE $3)'
                '    )'
                ') '
                f'ORDER BY h.{order_column} {order_direction}, h."id" {order_direction} '
                f'{pagination_sql}'
            ),
            params,
        )
        return [_host_from_row(row) for row in rows]

    query = using_read_connection(Host.filter(tenant_id=tenant_id))
    if search:
        query = query.filter(_host_search_condition(search)).distinct()

    direction_prefix = "" if sort_direction == "asc" else "-"
    query = query.order_by(f"{direction_prefix}{sort_by}", f"{direction_prefix}id")
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return await query


async def count_hosts_for_tenant(tenant_id: int, *, search: str = "") -> int:
    search = search.strip()
    if use_raw_queries():
        connection = get_read_connection()
        rows = await connection.execute_query_dict(
            (
                'SELECT COUNT(*) AS "count" '
                'FROM "host" h '
                'WHERE h."tenant_id" = $1 '
                'AND ('
                '    $2 = \'\' '
                '    OR h."ip"::text ILIKE $3 '
                '    OR h."id"::text = $2 '
                '    OR EXISTS ('
                '        SELECT 1 '
                '        FROM "hostport" hp '
                '        JOIN "port" p ON p."id" = hp."port_id" '
                '        WHERE hp."host_id" = h."id" '
                '        AND hp."tenant_id" = h."tenant_id" '
                '        AND (p."service_name" ILIKE $3 OR p."number"::text ILIKE $3)'
                '    )'
                ')'
            ),
            [tenant_id, search, f"%{search}%"],
        )
        return rows[0]["count"]

    query = using_read_connection(Host.filter(tenant_id=tenant_id))
    if search:
        query = query.filter(_host_search_condition(search)).distinct()
    return await query.count()


async def list_open_ports_by_host_for_tenant(
    tenant_id: int,
    host_ids: list[int] | None = None,
) -> dict[int, list[Port]]:
    if host_ids is not None and not host_ids:
        return {}

    if use_raw_queries():
        connection = get_read_connection()
        host_filter_sql = ""
        params: list[object] = [tenant_id]
        if host_ids is not None:
            placeholders = ", ".join(f"${index}" for index in range(2, len(host_ids) + 2))
            host_filter_sql = f'AND hp."host_id" IN ({placeholders}) '
            params.extend(host_ids)
        rows = await connection.execute_query_dict(
            (
                'SELECT '
                '    hp."host_id", p."id", p."number", p."service_name", '
                '    p."created_at", p."updated_at", p."tenant_id" '
                'FROM "hostport" hp '
                'JOIN "port" p ON p."id" = hp."port_id" '
                'WHERE hp."tenant_id" = $1 '
                f'{host_filter_sql}'
                'ORDER BY hp."host_id", p."number", p."service_name"'
            ),
            params,
        )
    else:
        query = using_read_connection(HostPort.filter(tenant_id=tenant_id))
        if host_ids is not None:
            query = query.filter(host_id__in=host_ids)
        rows = await query.select_related("port").order_by(
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
