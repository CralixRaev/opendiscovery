from tortoise import Model, fields, BaseDBAsyncClient


class Tenant(Model):
    name = fields.CharField(max_length=255, null=False, unique=True)

    def __str__(self) -> str:
        return self.name


async def create_tenant(connection: BaseDBAsyncClient, name: str) -> Tenant:
    tenant = Tenant(name=name)
    await tenant.save(using_db=connection)
    return tenant

async def find_tenant(connection: BaseDBAsyncClient, name: str) -> Tenant | None:
    return await Tenant.filter(name=name).using_db(connection).get_or_none()