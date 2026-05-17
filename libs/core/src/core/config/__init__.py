from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    postgres_url: PostgresDsn = 'postgres://postgres:pass@localhost:5432/postgres'
    database_use_raw_queries: bool = False
    backend_cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    backend_token_secret: str = 'dev-opendiscovery-token-secret-change-me'
    backend_token_ttl_seconds: int = 60 * 60 * 12
    backend_token_issuer: str = 'opendiscovery-backend'
    scanner_token_ttl_seconds: int = 60 * 60 * 24 * 30
    nats_url: str = 'nats://localhost:4222'
    nats_account: str = '$G'
    nats_auth_user: str = 'auth'
    nats_auth_password: str = 'auth'
    auth_issuer_seed: str = ''

    @property
    def backend_cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(',') if origin.strip()]
