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
