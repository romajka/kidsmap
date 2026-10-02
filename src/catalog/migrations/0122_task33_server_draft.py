from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [('catalog', '0121_task33_publication'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='ServerDraft', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('target_type', models.CharField(max_length=24)),
            ('target_id', models.PositiveBigIntegerField(null=True, blank=True)),
            ('schema_version', models.PositiveIntegerField(default=1)),
            ('source_version', models.PositiveBigIntegerField(default=0)),
            ('version', models.PositiveBigIntegerField(default=1)),
            ('fields', models.JSONField(default=dict)),
            ('photo_name', models.CharField(max_length=255, blank=True, default='')),
            ('saved_at', models.DateTimeField(auto_now=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='server_drafts', to=settings.AUTH_USER_MODEL)),
            ('materialized_place', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='origin_drafts', to='catalog.place')),
        ], options={'indexes': [models.Index(fields=['actor', 'target_type', 'target_id'], name='catalog_ser_actor_i_76e27e_idx')], 'constraints': [models.CheckConstraint(condition=models.Q(version__gte=1, schema_version__gte=1), name='server_draft_positive_versions'), models.CheckConstraint(condition=models.Q(target_id__isnull=True, source_version=0) | models.Q(target_id__isnull=False, source_version__gte=1), name='server_draft_source_for_target')]}),
    ]
