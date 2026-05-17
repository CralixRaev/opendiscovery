from typing import TypeVar

from tortoise import Model

from core.config import Config


settings = Config()
TModel = TypeVar('TModel', bound=Model)


def use_raw_queries() -> bool:
    return settings.database_use_raw_queries


def mark_from_db(model: TModel) -> TModel:
    model._saved_in_db = True
    return model
