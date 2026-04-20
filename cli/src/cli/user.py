import tortoise
import typer
from tortoise import Tortoise
from tortoise.transactions import in_transaction

from core.config import Config
from core.database.models import tenant, user

app = typer.Typer()

async def _create_user(username: str, password: str, tenant_name: str):
    await Tortoise.init(
        db_url=str(Config().postgres_url),
        modules={'models': ['core.database.models']}
    )
    async with in_transaction() as connection:
        tenant_object = await tenant.find_tenant(connection, tenant_name)
        user_object = await user.create_user(connection, username, password, tenant_object)

    print(f"Successfully created user {repr(user_object)}")

    await Tortoise.generate_schemas()

@app.command()
def create(username: str, password: str, tenant_name: str):
    tortoise.run_async(_create_user(username, password, tenant_name))

if __name__ == "__main__":
    app()