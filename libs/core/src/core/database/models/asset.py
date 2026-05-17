from tortoise import Model, fields

from core.database.fields import InetField


class Host(Model):
    ip = InetField(null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='hosts')

    def __str__(self) -> str:
        return self.ip


class Port(Model):
    number = fields.IntField(null=False)
    service_name = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='ports')

    def __str__(self) -> str:
        return f'{self.number}/{self.service_name}'


class HostPort(Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='host_ports')
    host = fields.ForeignKeyField('models.Host', related_name='host_ports')
    port = fields.ForeignKeyField('models.Port', related_name='host_ports')

    def __str__(self) -> str:
        return f'{self.host_id}:{self.port_id}'
