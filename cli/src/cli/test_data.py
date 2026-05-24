import tortoise
import typer
from tortoise import Tortoise

from core.database import build_tortoise_config
from core.database.seed_data import populate_test_data

app = typer.Typer()


async def _populate(
    tenants: int,
    users_per_tenant: int,
    scanners_per_tenant: int,
    scan_jobs_per_scanner: int,
    hosts_per_scan_job: int,
):
    await Tortoise.init(config=build_tortoise_config())
    data_set = await populate_test_data(
        tenant_count=tenants,
        users_per_tenant=users_per_tenant,
        scanners_per_tenant=scanners_per_tenant,
        scan_jobs_per_scanner=scan_jobs_per_scanner,
        hosts_per_scan_job=hosts_per_scan_job,
    )
    await Tortoise.close_connections()

    print(
        "Created test data: "
        f"{len(data_set.tenants)} tenants, "
        f"{len(data_set.users)} users, "
        f"{len(data_set.scanners)} scanners, "
        f"{len(data_set.scan_jobs)} scan jobs, "
        f"{len(data_set.host_discoveries)} host discoveries, "
        f"{len(data_set.port_discoveries)} port discoveries"
    )


@app.command()
def populate(
    tenants: int = 2,
    users_per_tenant: int = 2,
    scanners_per_tenant: int = 2,
    scan_jobs_per_scanner: int = 2,
    hosts_per_scan_job: int = 3,
):
    tortoise.run_async(
        _populate(
            tenants,
            users_per_tenant,
            scanners_per_tenant,
            scan_jobs_per_scanner,
            hosts_per_scan_job,
        )
    )
