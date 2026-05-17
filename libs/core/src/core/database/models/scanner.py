from tortoise import Model, fields


class Scanner(Model):
    name = fields.CharField(max_length=128, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    tenant = fields.ForeignKeyField('models.Tenant', related_name='scanners')

    def __str__(self) -> str:
        return self.name
