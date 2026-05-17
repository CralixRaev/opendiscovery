from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from scanner_token import decode_unverified_claims


TENANT_SUBJECT_PREFIX = "opendiscovery.tenants"


class ClientConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OPENDISCOVERY_",
        extra="ignore",
        populate_by_name=True,
    )

    nats_url: str = Field(default="nats://localhost:4222")
    scanner_token: str = Field()
    nats_subject: str | None = Field(default=None)
    client_name: str = Field(default="opendiscovery-scanner-client")

    @property
    def scanner_claims(self) -> dict:
        return decode_unverified_claims(self.scanner_token)

    @property
    def tenant_id(self) -> int:
        tenant_id = self.scanner_claims.get("tenant_id")
        if not isinstance(tenant_id, int):
            raise ValueError("scanner token must contain integer tenant_id")
        return tenant_id

    @property
    def scanner_id(self) -> int:
        scanner_id = self.scanner_claims.get("scanner_id")
        if not isinstance(scanner_id, int):
            raise ValueError("scanner token must contain integer scanner_id")
        return scanner_id

    @property
    def subject(self) -> str:
        if self.nats_subject:
            return self.nats_subject
        return f"{TENANT_SUBJECT_PREFIX}.{self.tenant_id}.scanners.{self.scanner_id}.jobs"

    def scan_job_status_subject(self, scan_job_id: int) -> str:
        return f"{self.subject}.{scan_job_id}.status"
