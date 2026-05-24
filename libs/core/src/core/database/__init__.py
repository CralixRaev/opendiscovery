from typing import TypeVar

from tortoise import Model, Tortoise
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import ConfigurationError
from tortoise.queryset import QuerySet

from core.config import Config


settings = Config()
TModel = TypeVar('TModel', bound=Model)
PRIMARY_CONNECTION_NAME = "default"
READ_REPLICA_CONNECTION_NAME = "read_replica"
MODEL_MODULES = ["core.database.models"]


def build_tortoise_config() -> dict:
    connections = {PRIMARY_CONNECTION_NAME: str(settings.postgres_url)}
    if settings.postgres_read_url is not None:
        connections[READ_REPLICA_CONNECTION_NAME] = str(settings.postgres_read_url)

    return {
        "connections": connections,
        "apps": {
            "models": {
                "models": MODEL_MODULES,
                "default_connection": PRIMARY_CONNECTION_NAME,
            },
        },
        "use_tz": True,
        "timezone": "UTC",
    }


def use_raw_queries() -> bool:
    return settings.database_use_raw_queries


def has_read_replica() -> bool:
    return settings.postgres_read_url is not None


def get_read_connection() -> BaseDBAsyncClient:
    if has_read_replica():
        try:
            return Tortoise.get_connection(READ_REPLICA_CONNECTION_NAME)
        except ConfigurationError:
            pass
    return Tortoise.get_connection(PRIMARY_CONNECTION_NAME)


def using_read_connection(query: QuerySet[TModel]) -> QuerySet[TModel]:
    return query.using_db(get_read_connection())


def mark_from_db(model: TModel) -> TModel:
    model._saved_in_db = True
    return model
