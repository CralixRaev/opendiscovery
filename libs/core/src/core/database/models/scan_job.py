from datetime import UTC, datetime
from enum import StrEnum

from tortoise import Model, fields

from core.database import mark_from_db, use_raw_queries, using_read_connection
from core.database.models.scanner import Scanner


class ScanJobStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    FINISHED = 'finished'
    FAILED = 'failed'


class ScanJob(Model):
    ip_network = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    finished_at = fields.DatetimeField(null=True)
    status = fields.CharEnumField(ScanJobStatus, max_length=32, null=False)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='scan_jobs')
    scanner = fields.ForeignKeyField('models.Scanner', related_name='scan_jobs')

    def __str__(self) -> str:
        return self.ip_network


async def create_scan_job(ip_network: str, tenant_id: int, scanner_id: int) -> ScanJob | None:
    if use_raw_queries():
        connection = ScanJob._meta.db
        rows = await connection.execute_query_dict(
            (
                'INSERT INTO "scanjob" ("ip_network", "created_at", "finished_at", "status", "tenant_id", "scanner_id") '
                'SELECT $1, NOW(), NULL, $2, s."tenant_id", s."id" '
                'FROM "scanner" s '
                'WHERE s."id" = $3 AND s."tenant_id" = $4 '
                'RETURNING "id", "ip_network", "created_at", "finished_at", "status", "tenant_id", "scanner_id"'
            ),
            [ip_network, ScanJobStatus.PENDING.value, scanner_id, tenant_id],
        )
        if not rows:
            return None
        return _scan_job_from_row(rows[0])

    scanner = await Scanner.get_or_none(id=scanner_id, tenant_id=tenant_id)
    if scanner is None:
        return None

    scan_job = ScanJob(
        ip_network=ip_network,
        status=ScanJobStatus.PENDING,
        tenant_id=tenant_id,
        scanner=scanner,
    )
    await scan_job.save()
    return scan_job


async def list_scan_jobs_for_tenant(tenant_id: int) -> list[ScanJob]:
    if use_raw_queries():
        connection = ScanJob._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT "id", "ip_network", "created_at", "finished_at", "status", "tenant_id", "scanner_id" '
                'FROM "scanjob" '
                'WHERE "tenant_id" = $1 '
                'ORDER BY "created_at" DESC, "id" DESC'
            ),
            [tenant_id],
        )
        return [_scan_job_from_row(row) for row in rows]

    return await using_read_connection(
        ScanJob.filter(tenant_id=tenant_id).order_by("-created_at", "-id")
    )


async def find_scan_job_for_scanner(
    scan_job_id: int,
    tenant_id: int,
    scanner_id: int,
) -> ScanJob | None:
    if use_raw_queries():
        connection = ScanJob._meta.db
        rows = await connection.execute_query_dict(
            (
                'SELECT "id", "ip_network", "created_at", "finished_at", "status", "tenant_id", "scanner_id" '
                'FROM "scanjob" '
                'WHERE "id" = $1 AND "tenant_id" = $2 AND "scanner_id" = $3 '
                'LIMIT 1'
            ),
            [scan_job_id, tenant_id, scanner_id],
        )
        if not rows:
            return None
        return _scan_job_from_row(rows[0])

    return await ScanJob.get_or_none(id=scan_job_id, tenant_id=tenant_id, scanner_id=scanner_id)


async def update_scan_job_status(
    scan_job_id: int,
    tenant_id: int,
    scanner_id: int,
    status: ScanJobStatus,
) -> ScanJob | None:
    finished_at_expr = 'NOW()' if status in {ScanJobStatus.FINISHED, ScanJobStatus.FAILED} else 'NULL'

    if use_raw_queries():
        connection = ScanJob._meta.db
        rows = await connection.execute_query_dict(
            (
                f'UPDATE "scanjob" '
                f'SET "status" = $1, "finished_at" = {finished_at_expr} '
                f'WHERE "id" = $2 AND "tenant_id" = $3 AND "scanner_id" = $4 '
                f'RETURNING "id", "ip_network", "created_at", "finished_at", "status", "tenant_id", "scanner_id"'
            ),
            [status.value, scan_job_id, tenant_id, scanner_id],
        )
        if not rows:
            return None
        return _scan_job_from_row(rows[0])

    scan_job = await ScanJob.get_or_none(id=scan_job_id, tenant_id=tenant_id, scanner_id=scanner_id)
    if scan_job is None:
        return None

    scan_job.status = status
    scan_job.finished_at = None
    if status in {ScanJobStatus.FINISHED, ScanJobStatus.FAILED}:
        scan_job.finished_at = datetime.now(UTC)
    await scan_job.save(update_fields=["status", "finished_at"])
    return scan_job


def _scan_job_from_row(row: dict) -> ScanJob:
    return mark_from_db(
        ScanJob(
            id=row['id'],
            ip_network=row['ip_network'],
            created_at=row['created_at'],
            finished_at=row['finished_at'],
            status=ScanJobStatus(row['status']),
            tenant_id=row['tenant_id'],
            scanner_id=row['scanner_id'],
        )
    )
