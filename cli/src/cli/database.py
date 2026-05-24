import tortoise
import typer
from tortoise import Tortoise

from core.database import build_tortoise_config

app = typer.Typer()

async def _init():
    await Tortoise.init(
        config=build_tortoise_config(),
    )

@app.command()
def init():
    tortoise.run_async(_init())

if __name__ == "__main__":
    app()
