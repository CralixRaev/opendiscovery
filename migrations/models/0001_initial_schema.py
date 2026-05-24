from tortoise import migrations
from tortoise.migrations import operations as ops
from core.database.fields import InetField
from core.database.models.scan_job import ScanJobStatus
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Tenant',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(unique=True, max_length=255)),
            ],
            options={'table': 'tenant', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Host',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('ip', InetField()),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='hosts', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'host', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Port',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('number', fields.IntField()),
                ('service_name', fields.CharField(max_length=128)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='ports', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'port', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='HostPort',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='host_ports', on_delete=OnDelete.CASCADE)),
                ('host', fields.ForeignKeyField('models.Host', source_field='host_id', db_constraint=True, to_field='id', related_name='host_ports', on_delete=OnDelete.CASCADE)),
                ('port', fields.ForeignKeyField('models.Port', source_field='port_id', db_constraint=True, to_field='id', related_name='host_ports', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'hostport', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Scanner',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=128)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='scanners', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'scanner', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ScanJob',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('ip_network', fields.CharField(max_length=128)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('finished_at', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('status', fields.CharEnumField(description='PENDING: pending\nRUNNING: running\nFINISHED: finished\nFAILED: failed', enum_type=ScanJobStatus, max_length=32)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='scan_jobs', on_delete=OnDelete.CASCADE)),
                ('scanner', fields.ForeignKeyField('models.Scanner', source_field='scanner_id', db_constraint=True, to_field='id', related_name='scan_jobs', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'scanjob', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ScanJobHostDiscovery',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='scan_job_host_discoveries', on_delete=OnDelete.CASCADE)),
                ('scan_job', fields.ForeignKeyField('models.ScanJob', source_field='scan_job_id', db_constraint=True, to_field='id', related_name='host_discoveries', on_delete=OnDelete.CASCADE)),
                ('host', fields.ForeignKeyField('models.Host', source_field='host_id', db_constraint=True, to_field='id', related_name='scan_job_discoveries', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'scanjobhostdiscovery', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='ScanJobPortDiscovery',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='scan_job_port_discoveries', on_delete=OnDelete.CASCADE)),
                ('scan_job', fields.ForeignKeyField('models.ScanJob', source_field='scan_job_id', db_constraint=True, to_field='id', related_name='port_discoveries', on_delete=OnDelete.CASCADE)),
                ('host_port', fields.ForeignKeyField('models.HostPort', source_field='host_port_id', db_constraint=True, to_field='id', related_name='scan_job_discoveries', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'scanjobportdiscovery', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='User',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('username', fields.CharField(unique=True, max_length=128)),
                ('hashed_password', fields.CharField(max_length=512)),
                ('tenant', fields.ForeignKeyField('models.Tenant', source_field='tenant_id', db_constraint=True, to_field='id', related_name='users', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'user', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
