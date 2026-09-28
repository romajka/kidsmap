"""Permission-scoped read model for the moderation queue; never mutates content."""
from django.urls import reverse
from catalog.models import Place, PlaceReview, SiteReview, SpecialistReview, VolunteerPlaceRevision
from catalog.services.moderation_sla import calculate_sla
from catalog.services.staff_roles import is_volunteer


MODELS = (('place', Place, 'place'), ('place_revision', VolunteerPlaceRevision, 'place'),
          ('place_review', PlaceReview, 'review'), ('site_review', SiteReview, 'review'),
          ('specialist_review', SpecialistReview, 'review'))


def allowed_kinds(user):
    if not (user.is_authenticated and user.is_active and user.is_staff) or is_volunteer(user):
        return set()
    return {kind for kind, model, _ in MODELS if user.has_perm(f'catalog.change_{"place" if kind == "place_revision" else model._meta.model_name}')}


def queue_rows(user, params, *, now):
    kinds = allowed_kinds(user)
    status = params.get('status', 'pending')
    if status not in {'pending', 'needs_changes', 'approved', 'rejected', 'all'}:
        status = 'pending'
    content_type = params.get('type', '')
    rows = []
    for kind, model, sla_type in MODELS:
        if kind not in kinds or content_type and content_type not in {kind, sla_type}:
            continue
        qs = model.objects.all()
        if kind == 'place':
            qs = qs.filter(deleted_at__isnull=True, is_temporary=False).exclude(volunteer_revision__status__in=['draft', 'pending', 'rejected'])
            raw_status = 'published' if status == 'approved' else status
        elif kind == 'place_revision':
            # Approved payload is now the public Place, not a second queue item.
            qs = qs.filter(place__deleted_at__isnull=True, place__is_temporary=False, place__owner__isnull=True).exclude(status='approved').select_related('place')
            raw_status = 'rejected' if status == 'needs_changes' else status
            if status == 'rejected':
                continue  # Rejected revision means needs changes, not final rejection.
        else:
            raw_status = status
            if status == 'needs_changes':
                continue
        if status != 'all':
            qs = qs.filter(status=raw_status)
        else:
            qs = qs.exclude(status='draft')
        for obj in qs.iterator():
            row_status = 'needs_changes' if kind == 'place_revision' and obj.status == 'rejected' else 'approved' if kind == 'place' and obj.status == 'published' else obj.status
            submitted = obj.submitted_at or obj.created_at
            paused = getattr(obj, 'needs_changes_at', None) or now if row_status == 'needs_changes' else None
            completed = obj.moderated_at or (getattr(obj, 'updated_at', None) or obj.created_at) if row_status in {'approved', 'rejected'} else None
            sla = calculate_sla(sla_type, submitted, now=now, paused_at=paused, completed_at=completed)
            if params.get('sla_status') and params['sla_status'] != sla.status:
                continue
            date = submitted.date().isoformat()
            if params.get('from') and date < params['from'] or params.get('to') and date > params['to']:
                continue
            place = obj.place if kind == 'place_revision' else obj if kind == 'place' else None
            name = (obj.payload.get('name_az') or place.name) if kind == 'place_revision' else place.name if place else (obj.text[:100] or f'#{obj.pk}')
            target_model = Place if kind == 'place_revision' else model
            target_pk = obj.place_id if kind == 'place_revision' else obj.pk
            rows.append({'kind': kind, 'content_type': sla_type, 'id': obj.pk, 'name': name,
                'status': row_status, 'submitted_at': submitted, 'estimated': obj.submitted_at is None,
                'sla': sla, 'age_hours': round(sla.elapsed_seconds / 3600, 1),
                'remaining_hours': round(sla.remaining_seconds / 3600, 1) if sla.remaining_seconds is not None else None,
                'url': reverse(f'admin:catalog_{target_model._meta.model_name}_change', args=[target_pk]),
                'needs_changes_url': reverse('admin:moderation_needs_changes', args=[obj.pk]) if kind == 'place' and row_status == 'pending' else ''})
    return sorted(rows, key=lambda row: (row['submitted_at'], row['kind'], row['id']))
