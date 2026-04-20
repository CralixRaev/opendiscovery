from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    postgres_url: PostgresDsn = 'postgres://postgres:pass@localhost:5432/postgres'