from tortoise import Model, fields, BaseDBAsyncClient

from core.database import mark_from_db, use_raw_queries


class Tenant(Model):
    name = fields.CharField(max_length=255, null=False, unique=True)

    def __str__(self) -> str:
        return self.name


async def create_tenant(connection: BaseDBAsyncClient, name: str) -> Tenant:
    if use_raw_queries():
        rows = await connection.execute_query_dict(
            'INSERT INTO "tenant" ("name") VALUES ($1) RETURNING "id", "name"',
            [name],
        )
        return _tenant_from_row(rows[0])

    tenant = Tenant(name=name)
    await tenant.save(using_db=connection)
    return tenant


async def find_tenant(connection: BaseDBAsyncClient, name: str) -> Tenant | None:
    if use_raw_queries():
        rows = await connection.execute_query_dict(
            'SELECT "id", "name" FROM "tenant" WHERE "name" = $1 LIMIT 1',
            [name],
        )
        if not rows:
            return None
        return _tenant_from_row(rows[0])

    return await Tenant.filter(name=name).using_db(connection).get_or_none()


def _tenant_from_row(row: dict) -> Tenant:
    return mark_from_db(Tenant(id=row['id'], name=row['name']))
