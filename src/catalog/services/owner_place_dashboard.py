"""Read-only owner cabinet projection; live and saved candidate stay separate."""
from catalog.models import PlacePhoto, PricingPlan
from catalog.services.permanent_place_rules import copy as text
from catalog.services.place_readiness import evaluate_place_readiness, evaluate_saved_place_readiness
from catalog.services.pricing_plans import legacy_price_values, normalize_pricing_plans, place_pricing_records
from catalog.services.volunteer_places import candidate_from_payload


def _saved_display(place, revision):
    candidate = candidate_from_payload(place, revision.payload)
    candidate._state.fields_cache = dict(candidate._state.fields_cache)
    candidate._public_file_exists_cache = {}
    payload = revision.payload
    if 'pricing_plans' in payload or 'nested_pricing' in payload:
        # Use the public formatter with in-memory canonical records. A candidate
        # must not fall back to old relational rows or their scalar projections.
        records = [plan for plan in place_pricing_records(place)
                   if (plan.offering_group_id is None and 'pricing_plans' not in payload)
                   or (plan.offering_group_id is not None and 'nested_pricing' not in payload)]
        batches = [payload.get('pricing_plans') or []]
        for activity in (payload.get('nested_pricing') or {}).get('activities', []):
            for group in activity.get('groups', []):
                batches.append(group.get('pricing_plans') or [])
        fields = {field.name: field for field in PricingPlan._meta.concrete_fields if not field.is_relation}
        # The tariff limit applies to each group, not the whole place.
        for values in batches:
            for row in normalize_pricing_plans(values, strict=False, validate_constraints=False):
                records.append(PricingPlan(**{name: fields[name].to_python(value)
                                             for name, value in row.items() if name in fields}))
        candidate._pricing_records_cache = records
        for name, value in legacy_price_values(records).items():
            setattr(candidate, name, value)
    photos, seen = [], set()
    gallery = ([PlacePhoto(image=row['image']).image for row in payload['gallery'] if row.get('image')]
               if 'gallery' in payload else [row.image for row in place.gallery.all()])
    for file in [candidate.photo or candidate.cover_photo, *gallery]:
        if candidate._public_file_exists(file) and file.name not in seen:
            seen.add(file.name)
            photos.append(file)
    candidate.gallery_files = lambda: photos
    return candidate


def project_owner_place(place, latest_request=None):
    """The controller sets fresh owner_can_edit before private data is read."""
    published = place.status == place.STATUS_PUBLISHED and place.is_active
    revision = getattr(place, 'volunteer_revision', None) if place.owner_can_edit else None
    # An unchanged published save can retain an empty revision for versioning.
    if revision and published and revision.status == 'draft' and not revision.payload:
        revision = None
    saved = bool(revision and revision.status in {'draft', 'pending', 'rejected'})
    state = place.status
    note = place.rejection_reason if place.owner_can_edit else ''
    if revision:
        state = {'rejected': 'needs_changes', 'declined': 'rejected',
                 'approved': 'published' if published else 'approved'}.get(revision.status, revision.status)
        note = revision.review_note if revision.status in {'draft', 'rejected', 'declined'} else ''
    elif latest_request and latest_request.request_kind == latest_request.KIND_PUBLICATION:
        state = {'PENDING': 'pending', 'REJECTED': 'needs_changes',
                 'APPROVED': 'published' if published else 'approved'}.get(latest_request.status, state)
        if place.owner_can_edit and latest_request.status == latest_request.STATUS_REJECTED:
            note = latest_request.moderation_note or note
    labels = {
        'draft': text('Черновик', 'Qaralama', 'Draft'),
        'pending': text('На модерации', 'Moderasiyada', 'In review'),
        'needs_changes': text('Нужна доработка', 'Düzəliş lazımdır', 'Needs changes'),
        'rejected': text('Отклонено', 'Rədd edilib', 'Declined'),
        'approved': text('Одобрено', 'Təsdiqlənib', 'Approved'),
        'published': text('Опубликовано', 'Dərc olunub', 'Published'),
    }
    place.owner_workflow = {
        'status': state, 'label': labels.get(state, labels['draft']),
        'pending': state == 'pending', 'needs_changes': state in {'needs_changes', 'rejected'},
        'review_note': note, 'saved_candidate': saved,
        'show_changes': bool(published and revision and revision.status != 'approved'),
        'css': 'pending' if state == 'pending' else 'rejected' if state in {'needs_changes', 'rejected'}
               else 'approved' if state in {'approved', 'published'} else 'draft',
    }
    place.owner_saved_display = _saved_display(place, revision) if saved else place
    place.owner_display = place if published else place.owner_saved_display
    place.owner_photo_count = len(place.owner_display.gallery_files())
    # No actor-private ServerDraft is merged here: its own card stays distinct.
    return evaluate_saved_place_readiness(place) if place.owner_can_edit else evaluate_place_readiness(place)
