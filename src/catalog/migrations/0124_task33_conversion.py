from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('catalog', '0123_task33_group_pricing')]
    operations = [
        migrations.CreateModel(name='ConversionRun', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('plan_digest', models.CharField(max_length=64, unique=True)),
            ('rule_version', models.PositiveIntegerField()),
            ('entry_count', models.PositiveIntegerField()),
            ('baseline_counts', models.JSONField(default=dict)),
            ('checkpoint', models.PositiveIntegerField(default=0)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ], options={'constraints': [models.CheckConstraint(condition=Q(checkpoint__gte=0), name='conversion_run_checkpoint_nonnegative')]}),
        migrations.CreateModel(name='ConversionMapping', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('source_type', models.CharField(max_length=32)),
            ('source_id', models.PositiveBigIntegerField()),
            ('rule_version', models.PositiveIntegerField()),
            ('piece_key', models.CharField(max_length=48)),
            ('source_version', models.PositiveBigIntegerField(blank=True, null=True)),
            ('source_fingerprint', models.CharField(max_length=64)),
            ('target_type', models.CharField(blank=True, max_length=32)),
            ('target_id', models.PositiveBigIntegerField(blank=True, null=True)),
            ('state', models.CharField(choices=[('applied', 'applied'), ('manual_review', 'manual_review')], max_length=16)),
            ('reason_code', models.CharField(max_length=48)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('run', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mappings', to='catalog.conversionrun')),
        ], options={'constraints': [models.UniqueConstraint(fields=('source_type', 'source_id', 'rule_version', 'piece_key'), name='conversion_piece_unique'), models.CheckConstraint(condition=(Q(state='applied', target_id__isnull=False) & ~Q(target_type='')) | Q(state='manual_review', target_type='', target_id__isnull=True), name='conversion_mapping_target_state')], 'indexes': [models.Index(fields=('state', 'reason_code'), name='conversion_review_idx')]}),
    ]
