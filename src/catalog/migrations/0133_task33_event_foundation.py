"""Conservative Event foundation: no organizer or historic venue inference."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def reconcile_legacy_events(apps, schema_editor):
    Event = apps.get_model('catalog', 'Event')
    db = schema_editor.connection.alias
    for event in Event.objects.using(db).all().iterator():
        changes = {}
        if event.status in ('expired', 'cancelled'):
            changes['legacy_publication_status'] = event.status
            changes['status'] = 'published' if event.published_at is not None else 'draft'
            if event.status == 'cancelled':
                changes['occurrence_state'] = 'cancelled'
        approved = changes.get('status', event.status) == 'published'
        if approved and not event.venue_snapshot:
            changes['venue_snapshot'] = {
                'label': '', 'address': event.address or '', 'district': event.district or '',
                'metro': event.metro or '', 'lat': str(event.lat) if event.lat is not None else None,
                'lng': str(event.lng) if event.lng is not None else None,
            }
        if changes:
            Event.objects.using(db).filter(pk=event.pk).update(**changes)


def restore_legacy_statuses(apps, schema_editor):
    Event = apps.get_model('catalog', 'Event')
    db = schema_editor.connection.alias
    for status in ('expired', 'cancelled'):
        Event.objects.using(db).filter(legacy_publication_status=status).update(status=status)


class Migration(migrations.Migration):
    dependencies = [('catalog', '0132_task33_specialist_foundation'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='event', name='organizer_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='organized_events', to='catalog.organization')),
        migrations.AddField(model_name='event', name='organizer_specialist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='organized_events', to='catalog.specialist')),
        migrations.AddField(model_name='event', name='organizer_resolution',
            field=models.CharField(choices=[('resolved', 'Resolved'), ('legacy_unresolved', 'Legacy unresolved')],
                default='legacy_unresolved', editable=False, max_length=24)),
        migrations.AddField(model_name='event', name='event_format',
            field=models.CharField(choices=[('physical', 'Очно'), ('online', 'Онлайн')], default='physical', max_length=16)),
        migrations.AddField(model_name='event', name='occurrence_state',
            field=models.CharField(choices=[('scheduled', 'Запланировано'), ('cancelled', 'Отменено'), ('rescheduled', 'Перенесено')],
                default='scheduled', editable=False, max_length=16)),
        migrations.AddField(model_name='event', name='occurrence_version', field=models.PositiveIntegerField(default=0, editable=False)),
        migrations.AddField(model_name='event', name='venue_label', field=models.CharField(blank=True, default='', max_length=255)),
        migrations.AddField(model_name='event', name='venue_snapshot', field=models.JSONField(default=dict, editable=False)),
        migrations.AddField(model_name='event', name='legacy_publication_status',
            field=models.CharField(blank=True, default='', editable=False, max_length=16)),
        migrations.RunPython(reconcile_legacy_events, restore_legacy_statuses),
        migrations.AlterField(model_name='event', name='status',
            field=models.CharField(choices=[('draft', 'Черновик'), ('pending', 'На модерации'), ('published', 'Опубликовано'),
                ('rejected', 'Отклонено')], db_index=True, default='draft', max_length=16, verbose_name='Статус модерации')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(condition=(
            models.Q(organizer_resolution='resolved', organizer_organization__isnull=False, organizer_specialist__isnull=True)
            | models.Q(organizer_resolution='resolved', organizer_organization__isnull=True, organizer_specialist__isnull=False)
            | models.Q(organizer_resolution='legacy_unresolved', organizer_organization__isnull=True, organizer_specialist__isnull=True)
        ), name='event_organizer_xor')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(
            condition=models.Q(event_format__in=('physical', 'online')), name='event_valid_format')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(
            condition=models.Q(occurrence_state__in=('scheduled', 'cancelled', 'rescheduled')), name='event_valid_occurrence')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(
            condition=models.Q(status__in=('draft', 'pending', 'published', 'rejected')), name='event_valid_publication')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(condition=(
            models.Q(organizer_resolution='legacy_unresolved') | models.Q(start_datetime__isnull=True)
            | models.Q(end_datetime__isnull=True) | models.Q(end_datetime__gt=models.F('start_datetime'))),
            name='event_resolved_positive_interval')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(condition=(
            ~models.Q(organizer_resolution='resolved', status='published')
            | models.Q(start_datetime__isnull=False, end_datetime__isnull=False)), name='event_resolved_publication_dates')),
        migrations.AddConstraint(model_name='event', constraint=models.CheckConstraint(condition=(models.Q(event_format='physical')
            | models.Q(related_place__isnull=True, lat__isnull=True, lng__isnull=True, address='', district='', metro='',
                venue_label='', venue_snapshot={})), name='event_online_no_geography')),
        migrations.CreateModel(name='EventOccurrenceChange', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('kind', models.CharField(choices=[('cancel', 'Cancel'), ('reschedule', 'Reschedule')], max_length=16)),
            ('version', models.PositiveIntegerField(default=1)),
            ('reason', models.TextField(blank=True, default='')),
            ('before', models.JSONField(default=dict)), ('after', models.JSONField(default=dict)),
            ('happened_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='+', to=settings.AUTH_USER_MODEL)),
            ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='occurrence_changes', to='catalog.event')),
        ], options={'ordering': ('version', 'pk'), 'constraints': [
            models.UniqueConstraint(fields=('event', 'version'), name='event_occurrence_unique_version'),
            models.CheckConstraint(condition=models.Q(version__gte=1), name='event_occurrence_positive_version'),
            models.CheckConstraint(condition=models.Q(kind__in=('cancel', 'reschedule')), name='event_occurrence_valid_kind'),
        ]}),
    ]
