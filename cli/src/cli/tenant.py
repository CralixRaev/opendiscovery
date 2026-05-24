import tortoise
import typer
from tortoise import Tortoise
from tortoise.transactions import in_transaction

from core.database import build_tortoise_config
from core.database.models.tenant import create_tenant

app = typer.Typer()

async def _create_tenant(name: str):
    await Tortoise.init(
        config=build_tortoise_config(),
    )

    async with in_transaction() as connection:
        tenant = await create_tenant(connection, name)
    print(f"Successfully created tenant {repr(tenant)}")

@app.command()
def create(name: str):
    tortoise.run_async(_create_tenant(name))

if __name__ == "__main__":
    app()
