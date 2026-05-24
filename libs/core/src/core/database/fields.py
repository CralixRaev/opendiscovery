from typing import Any

from tortoise import fields


class InetField(fields.CharField):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=45, **kwargs)

    @property
    def SQL_TYPE(self) -> str:
        return 'INET'
