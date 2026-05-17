from tortoise import Model, fields, BaseDBAsyncClient

from core import utils
from core.database import mark_from_db, use_raw_queries
from core.database.models import Tenant


class User(Model):
    username = fields.CharField(max_length=128, null=False, unique=True)
    hashed_password = fields.CharField(max_length=512, null=False)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='users')


async def create_user(connection: BaseDBAsyncClient, username: str, password: str, tenant: Tenant) -> User:
    hashed_password = utils.password.hash_password(password)
    if use_raw_queries():
        rows = await connection.execute_query_dict(
            (
                'INSERT INTO "user" ("username", "hashed_password", "tenant_id") '
                'VALUES ($1, $2, $3) '
                'RETURNING "id", "username", "hashed_password", "tenant_id"'
            ),
            [username, hashed_password, tenant.id],
        )
        return _user_from_row(rows[0], tenant=tenant)

    user = User(username=username, hashed_password=hashed_password, tenant=tenant)
    await user.save(using_db=connection)
    return user


async def find_user_for_login(username: str, tenant_name: str) -> User | None:
    if use_raw_queries():
        connection = User._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT '
                'u."id", u."username", u."hashed_password", u."tenant_id", '
                't."id" AS "tenant__id", t."name" AS "tenant__name" '
                'FROM "user" u '
                'JOIN "tenant" t ON t."id" = u."tenant_id" '
                'WHERE u."username" = $1 AND t."name" = $2 '
                'LIMIT 1'
            ),
            [username, tenant_name],
        )
        if not rows:
            return None
        return _user_from_joined_row(rows[0])

    return await User.get_or_none(
        username=username,
        tenant__name=tenant_name,
    ).select_related("tenant")


async def find_user_by_id_and_tenant(user_id: int, tenant_id: int) -> User | None:
    if use_raw_queries():
        connection = User._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT '
                'u."id", u."username", u."hashed_password", u."tenant_id", '
                't."id" AS "tenant__id", t."name" AS "tenant__name" '
                'FROM "user" u '
                'JOIN "tenant" t ON t."id" = u."tenant_id" '
                'WHERE u."id" = $1 AND u."tenant_id" = $2 '
                'LIMIT 1'
            ),
            [user_id, tenant_id],
        )
        if not rows:
            return None
        return _user_from_joined_row(rows[0])

    return await User.get_or_none(
        id=user_id,
        tenant_id=tenant_id,
    ).select_related("tenant")


def _user_from_joined_row(row: dict) -> User:
    tenant = mark_from_db(Tenant(id=row['tenant__id'], name=row['tenant__name']))
    return _user_from_row(row, tenant=tenant)


def _user_from_row(row: dict, tenant: Tenant | None = None) -> User:
    user = mark_from_db(
        User(
            id=row['id'],
            username=row['username'],
            hashed_password=row['hashed_password'],
            tenant_id=row['tenant_id'],
        )
    )
    if tenant is not None:
        object.__setattr__(user, 'tenant', tenant)
    return user
