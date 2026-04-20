from tortoise import Model, fields, BaseDBAsyncClient

from core import utils
from core.database.models import Tenant


class User(Model):
    username = fields.CharField(max_length=128, null=False, unique=True)
    hashed_password = fields.CharField(max_length=512, null=False)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='users')

async def create_user(connection: BaseDBAsyncClient, username: str, password: str, tenant: Tenant) -> User:
    hashed_password = utils.password.hash_password(password)
    user = User(username=username, hashed_password=hashed_password, tenant=tenant)
    await user.save(using_db=connection)
    return user