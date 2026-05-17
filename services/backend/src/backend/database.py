from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError, DBConnectionError

from core.config import Config
from core.database import READ_REPLICA_CONNECTION_NAME, build_tortoise_config, has_read_replica
from backend.nats import connect_nats, disconnect_nats


settings = Config()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await Tortoise.init(
        config=build_tortoise_config(),
        _enable_global_fallback=True,
    )
    await connect_nats(app)
    try:
        yield
    finally:
        await disconnect_nats(app)
        await Tortoise.close_connections()


async def is_database_ready() -> bool:
    try:
        connection = Tortoise.get_connection("default")
        await connection.execute_query("SELECT 1")
        if has_read_replica():
            read_connection = Tortoise.get_connection(READ_REPLICA_CONNECTION_NAME)
            await read_connection.execute_query("SELECT 1")
    except (ConfigurationError, DBConnectionError, RuntimeError):
        return False
    return True
