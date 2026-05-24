from datetime import UTC, datetime

import factory
from tortoise import Tortoise

from core import utils
from core.database import mark_from_db
from core.database.models import Host, HostPort, Port, ScanJob, Scanner, Tenant, User
from core.database.models.scan_job import ScanJobStatus

Tortoise.init_models(["core.database.models"], "models")


class TortoiseFactory(factory.Factory):
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return mark_from_db(model_class(*args, **kwargs))


class TenantFactory(TortoiseFactory):
    class Meta:
        model = Tenant

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f"tenant-{n}")


class UserFactory(TortoiseFactory):
    class Meta:
        model = User
        exclude = ("password",)

    id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user-{n}")
    password = "password"
    hashed_password = factory.LazyAttribute(lambda user: utils.password.hash_password(user.password))
    tenant = factory.SubFactory(TenantFactory)


class ScannerFactory(TortoiseFactory):
    class Meta:
        model = Scanner

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f"scanner-{n}")
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    tenant = factory.SubFactory(TenantFactory)


class ScanJobFactory(TortoiseFactory):
    class Meta:
        model = ScanJob

    id = factory.Sequence(lambda n: n + 1)
    ip_network = factory.Sequence(lambda n: f"10.{n % 255}.0.0/24")
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    finished_at = None
    status = ScanJobStatus.PENDING
    scanner = factory.SubFactory(ScannerFactory)
    tenant = factory.SelfAttribute("scanner.tenant")


class HostFactory(TortoiseFactory):
    class Meta:
        model = Host

    id = factory.Sequence(lambda n: n + 1)
    ip = factory.Sequence(lambda n: f"10.0.{n // 254}.{n % 254 + 1}")
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
    tenant = factory.SubFactory(TenantFactory)


class PortFactory(TortoiseFactory):
    class Meta:
        model = Port

    id = factory.Sequence(lambda n: n + 1)
    number = factory.Iterator([22, 80, 443, 5432, 8000])
    service_name = factory.Iterator(["ssh", "http", "https", "postgresql", "http-alt"])
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
    tenant = factory.SubFactory(TenantFactory)


class HostPortFactory(TortoiseFactory):
    class Meta:
        model = HostPort

    id = factory.Sequence(lambda n: n + 1)
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
    host = factory.SubFactory(HostFactory)
    port = factory.SubFactory(PortFactory, tenant=factory.SelfAttribute("..host.tenant"))
    tenant = factory.SelfAttribute("host.tenant")
