import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('catalog', '0136_retire_optional_listing_verification'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='OrganizationConnectionOperation', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('action', models.CharField(max_length=8, choices=[('connect','connect'), ('detach','detach')])),
            ('relationship_kind', models.CharField(max_length=16)),
            ('status', models.CharField(max_length=12, default='preview')),
            ('idempotency_key', models.UUIDField(null=True, blank=True)),
            ('fingerprint', models.CharField(max_length=64)),
            ('expires_at', models.DateTimeField()),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('actor', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
            ('organization', models.ForeignKey(to='catalog.organization', on_delete=django.db.models.deletion.PROTECT)),
        ], options={'constraints': [
            models.UniqueConstraint(fields=('actor','idempotency_key'), condition=models.Q(idempotency_key__isnull=False), name='org_connection_actor_key_unique'),
            models.CheckConstraint(condition=models.Q(action__in=['connect','detach']), name='org_connection_action_known'),
            models.CheckConstraint(condition=models.Q(status__in=['preview','running','completed']), name='org_connection_status_known'),
            models.CheckConstraint(condition=models.Q(relationship_kind__in=['business','informational']), name='org_connection_kind_known'),
        ]}),
        migrations.CreateModel(name='OrganizationConnectionItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('snapshot', models.JSONField(default=dict)),
            ('decision', models.CharField(max_length=24)),
            ('result', models.CharField(max_length=24, blank=True, default='')),
            ('completed_at', models.DateTimeField(null=True, blank=True)),
            ('operation', models.ForeignKey(to='catalog.organizationconnectionoperation', related_name='items', on_delete=django.db.models.deletion.CASCADE)),
            ('place', models.ForeignKey(to='catalog.place', on_delete=django.db.models.deletion.PROTECT)),
            ('request', models.ForeignKey(to='catalog.organizationplacerequest', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
        ], options={'ordering':['place_id'], 'constraints':[models.UniqueConstraint(fields=('operation','place'), name='org_connection_place_unique')]}),
    ]
