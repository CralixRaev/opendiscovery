from enum import StrEnum

from tortoise import Model, fields


class ScanJobStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    FINISHED = 'finished'
    FAILED = 'failed'


class ScanJob(Model):
    name = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    finished_at = fields.DatetimeField(null=True)
    status = fields.CharEnumField(ScanJobStatus, max_length=32, null=False)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='scan_jobs')
    scanner = fields.ForeignKeyField('models.Scanner', related_name='scan_jobs')

    def __str__(self) -> str:
        return self.name
