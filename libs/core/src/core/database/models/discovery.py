from tortoise import Model, fields


class ScanJobHostDiscovery(Model):
    tenant = fields.ForeignKeyField(
        'models.Tenant',
        related_name='scan_job_host_discoveries',
    )
    scan_job = fields.ForeignKeyField('models.ScanJob', related_name='host_discoveries')
    host = fields.ForeignKeyField('models.Host', related_name='scan_job_discoveries')


class ScanJobPortDiscovery(Model):
    tenant = fields.ForeignKeyField(
        'models.Tenant',
        related_name='scan_job_port_discoveries',
    )
    scan_job = fields.ForeignKeyField('models.ScanJob', related_name='port_discoveries')
    host_port = fields.ForeignKeyField(
        'models.HostPort',
        related_name='scan_job_discoveries',
    )
