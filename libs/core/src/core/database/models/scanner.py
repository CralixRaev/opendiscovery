from datetime import datetime

from tortoise import Model, fields

from core.database import mark_from_db, use_raw_queries
from core.database.models.tenant import Tenant


class Scanner(Model):
    name = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='scanners')

    def __str__(self) -> str:
        return self.name


async def create_scanner(name: str, tenant: Tenant) -> Scanner:
    if use_raw_queries():
        connection = Scanner._meta.db
        rows = await connection.execute_query_dict(
            (
                'INSERT INTO "scanner" ("name", "created_at", "tenant_id") '
                'VALUES ($1, NOW(), $2) '
                'RETURNING "id", "name", "created_at", "tenant_id"'
            ),
            [name, tenant.id],
        )
        return _scanner_from_row(rows[0], tenant=tenant)

    scanner = Scanner(name=name, tenant=tenant)
    await scanner.save()
    return scanner


async def list_scanners_for_tenant(tenant_id: int) -> list[Scanner]:
    if use_raw_queries():
        connection = Scanner._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT "id", "name", "created_at", "tenant_id" '
                'FROM "scanner" '
                'WHERE "tenant_id" = $1 '
                'ORDER BY "created_at" DESC, "id" DESC'
            ),
            [tenant_id],
        )
        return [_scanner_from_row(row) for row in rows]

    return await Scanner.filter(tenant_id=tenant_id).order_by("-created_at", "-id")


def _scanner_from_row(row: dict, tenant: Tenant | None = None) -> Scanner:
    scanner = mark_from_db(
        Scanner(
            id=row['id'],
            name=row['name'],
            created_at=_normalize_created_at(row['created_at']),
            tenant_id=row['tenant_id'],
        )
    )
    if tenant is not None:
        object.__setattr__(scanner, 'tenant', tenant)
    return scanner


def _normalize_created_at(value: datetime | str) -> datetime | str:
    if isinstance(value, str):
        return value
    return value
