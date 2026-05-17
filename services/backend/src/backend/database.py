from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError

from core.config import Config


settings = Config()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await Tortoise.init(
        db_url=str(settings.postgres_url),
        modules={"models": ["core.database.models"]},
        _enable_global_fallback=True,
    )
    try:
        yield
    finally:
        await Tortoise.close_connections()


async def is_database_ready() -> bool:
    try:
        connection = Tortoise.get_connection("default")
        await connection.execute_query("SELECT 1")
    except (DBConnectionError, RuntimeError):
        return False
    return True
