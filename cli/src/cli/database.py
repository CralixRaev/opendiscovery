import tortoise
import typer
from tortoise import Tortoise

from core.config import Config

app = typer.Typer()

async def _init():
    await Tortoise.init(
        db_url=str(Config().postgres_url),
        modules={'models': ['core.database.models']}
    )
    await Tortoise.generate_schemas()

@app.command()
def init():
    tortoise.run_async(_init())

if __name__ == "__main__":
    app()