"""Event occurrence audit and model invariants; actor rights live in the service."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ImmutableOccurrenceQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Occurrence history cannot be overwritten.')

    def delete(self):
        raise ValidationError('Occurrence history cannot be deleted.')

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Occurrence history cannot be overwritten.')

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False,
                    update_conflicts=False, update_fields=None, unique_fields=None):
        if update_conflicts:
            raise ValidationError('Occurrence history cannot be overwritten.')
        return super().bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=False, update_fields=update_fields, unique_fields=unique_fields)


class EventOccurrenceChange(models.Model):
    CANCEL = 'cancel'
    RESCHEDULE = 'reschedule'
    event = models.ForeignKey('catalog.Event', on_delete=models.PROTECT, related_name='occurrence_changes')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    kind = models.CharField(max_length=16, choices=((CANCEL, 'Cancel'), (RESCHEDULE, 'Reschedule')))
    version = models.PositiveIntegerField(default=1)
    reason = models.TextField(blank=True, default='')
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    happened_at = models.DateTimeField(default=timezone.now, editable=False)
    objects = ImmutableOccurrenceQuerySet.as_manager()

    def save(self, *args, **kwargs):
        # Caller-supplied PKs can otherwise turn a newly constructed model into
        # an UPDATE through Django's normal save fallback. Audit IDs are generated.
        if not self._state.adding or self.pk is not None:
            raise ValidationError('Occurrence history cannot be overwritten.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Occurrence history cannot be deleted.')

    class Meta:
        ordering = ('version', 'pk')
        constraints = [
            models.UniqueConstraint(fields=('event', 'version'), name='event_occurrence_unique_version'),
            models.CheckConstraint(condition=Q(version__gte=1), name='event_occurrence_positive_version'),
            models.CheckConstraint(condition=Q(kind__in=('cancel', 'reschedule')), name='event_occurrence_valid_kind'),
        ]


def _approved_occurrence(event):
    # A retained physical snapshot proves prior approval even when the original
    # approval timestamp is unknown and the publication has returned to draft.
    return event.published_at is not None or event.status == event.STATUS_PUBLISHED or bool(event.venue_snapshot)


def validate_event_format_history(event, original):
    if (original and _approved_occurrence(original) and event.event_format != original.event_format
            and not getattr(event, '_allow_occurrence_change', False)):
        raise ValidationError({'event_format': 'Approved event format cannot change through content editing.'})


def validate_event_domain(event, original=None):
    validate_event_format_history(event, original)
    errors = {}
    if event.organizer_organization_id or event.organizer_specialist_id:
        event.organizer_resolution = event.ORGANIZER_RESOLVED
    resolved = event.organizer_resolution == event.ORGANIZER_RESOLVED
    organizers = bool(event.organizer_organization_id) + bool(event.organizer_specialist_id)
    if organizers != (1 if resolved else 0):
        errors['organizer_organization'] = 'Choose exactly one organizer.'
    if event.event_format not in (event.FORMAT_PHYSICAL, event.FORMAT_ONLINE):
        errors['event_format'] = 'Invalid event format.'
    if event.occurrence_state not in (event.OCCURRENCE_SCHEDULED, event.OCCURRENCE_CANCELLED, event.OCCURRENCE_RESCHEDULED):
        errors['occurrence_state'] = 'Invalid occurrence state.'
    for name in ('start_datetime', 'end_datetime'):
        value = getattr(event, name)
        if value is not None and timezone.is_naive(value):
            errors[name] = 'Use an aware date and time.'
    if not errors and event.start_datetime and event.end_datetime and event.end_datetime <= event.start_datetime:
        errors['end_datetime'] = 'End must be after start.'
    if resolved and event.status == event.STATUS_PUBLISHED and (not event.start_datetime or not event.end_datetime):
        errors['start_datetime'] = 'Publication requires an exact interval.'
    if not isinstance(event.venue_snapshot, dict):
        errors['venue_snapshot'] = 'Venue snapshot must be an object.'
    if original:
        approved = _approved_occurrence(original)
        date_changed = (event.start_datetime, event.end_datetime) != (original.start_datetime, original.end_datetime)
        occurrence_changed = event.occurrence_state != original.occurrence_state
        snapshot_changed = event.venue_snapshot != original.venue_snapshot
        authorized_change = bool(getattr(event, '_allow_occurrence_change', False))
        if approved and date_changed and original.start_datetime and original.start_datetime <= timezone.now():
            errors['start_datetime'] = 'A started occurrence needs a new Event ID.'
        if approved and (date_changed or occurrence_changed) and not authorized_change:
            errors['occurrence_state'] = 'Use the recorded occurrence change service.'
        if original.venue_snapshot and snapshot_changed and not authorized_change:
            errors['venue_snapshot'] = 'Approved venue history is immutable.'
    if errors:
        raise ValidationError(errors)
