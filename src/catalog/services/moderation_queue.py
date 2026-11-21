"""Permission-scoped read model for the moderation queue; never mutates content."""
from django.contrib.auth import get_user_model
from django.db.models import Case, Exists, F, OuterRef, Q, Subquery, Value, When
from django.urls import reverse

from catalog.models import OrganizationPlaceRequest, Place, SiteReview, VolunteerPlaceRevision
from catalog.services.moderation_sla import calculate_sla, matches_submission_date
from catalog.services.review_versions import review_types
from catalog.services.staff_roles import is_volunteer


TYPED_REVIEWS = {f'{kind}_review': (head, revision)
                 for kind, (_, head, revision, _) in review_types().items()}
PROPOSAL_TYPES = ('organization', 'program', 'activity', 'offering_group')
REVISION_STATUSES = {'rejected': 'needs_changes', 'declined': 'rejected'}
STORED_REVISION_STATUSES = {state: stored for stored, state in REVISION_STATUSES.items()}


def actionable_place_filter():
    """Pending candidate wins over the card's historical publication status.

    Legacy cards without a candidate still use their own pending flag. A draft,
    returned or decided candidate must not reappear because that flag is stale.
    The revision relation is one-to-one, so every place is selected only once.
    """
    return Q(deleted_at__isnull=True, is_temporary=False) & (
        Q(volunteer_revision__status=VolunteerPlaceRevision.Status.PENDING)
        | Q(status=Place.STATUS_PENDING, volunteer_revision__isnull=True)
    )


def allowed_kinds(user):
    if not (user.is_authenticated and user.is_active and user.is_staff) or is_volunteer(user):
        return set()
    models = {'place': Place, 'place_revision': Place, 'site_review': SiteReview,
              **{kind: head for kind, (head, _) in TYPED_REVIEWS.items()}}
    kinds = {kind for kind, model in models.items() if user.has_perm(f'catalog.change_{model._meta.model_name}')}
    if user.has_perm('catalog.change_placeownershiprequest'):
        kinds.add('affiliation')
    return kinds


def matches_queue_type(kind, content_type, selected):
    return not selected or selected in (kind, content_type) or (
        selected == 'proposals' and content_type in PROPOSAL_TYPES
    )


def _row(kind, content_type, pk, name, status, source, now, url, needs_changes_url=''):
    # Affiliation requests enter moderation on creation. Older content imports
    # can lack an explicit submission date, which the UI marks as approximate.
    actual_submission = getattr(source, 'submitted_at', source.created_at)
    submitted = actual_submission or source.created_at
    paused = completed = None
    if status == 'needs_changes':
        paused = source.needs_changes_at or source.moderated_at or getattr(source, 'updated_at', None) or submitted
    elif status in ('approved', 'rejected', 'canceled'):
        completed = (getattr(source, 'decided_at', None) or getattr(source, 'moderated_at', None)
                     or getattr(source, 'updated_at', None) or submitted)
    sla = calculate_sla(content_type, submitted, now=now, paused_at=paused, completed_at=completed)
    return {'kind': kind, 'content_type': content_type, 'id': pk, 'name': name, 'status': status,
            'submitted_at': submitted, 'estimated': actual_submission is None, 'sla': sla,
            'url': url, 'needs_changes_url': needs_changes_url}


def _places(status, selected, now):
    if matches_queue_type('place', 'place', selected):
        # A working or finally refused revision has its own queue row.
        places = (Place.objects.filter(deleted_at__isnull=True, is_temporary=False)
            .filter(Q(volunteer_revision__isnull=True) | Q(volunteer_revision__status='approved'))
            .select_related('volunteer_revision')
            .only('status', 'name', 'created_at', 'updated_at', 'submitted_at', 'needs_changes_at', 'moderated_at',
                  'volunteer_revision__created_at', 'volunteer_revision__updated_at', 'volunteer_revision__submitted_at',
                  'volunteer_revision__moderated_at')
            .annotate(queue_status=Case(
                When(status='published', then=Value('approved')),
                When(status='pending', volunteer_revision__status='approved', then=Value('approved')),
                default=F('status'))))
        if status == 'all':
            places = places.exclude(status='draft')
        else:
            places = places.filter(queue_status=status)
        for place in places.iterator():
            state = place.queue_status
            source = getattr(place, 'volunteer_revision', None) if state == 'approved' else None
            yield _row('place', 'place', place.pk, place.name, state, source or place, now,
                       reverse('admin:catalog_place_change', args=[place.pk]),
                       reverse('admin:moderation_needs_changes', args=[place.pk]) if state == 'pending' else '')
    if not matches_queue_type('place_revision', 'place', selected):
        return
    revisions = (VolunteerPlaceRevision.objects.filter(place__deleted_at__isnull=True, place__is_temporary=False)
        .exclude(status__in=('draft', 'approved')).select_related('place')
        .only('status', 'payload', 'created_at', 'updated_at', 'submitted_at',
              'needs_changes_at', 'moderated_at', 'place__name'))
    if status != 'all':
        db_status = STORED_REVISION_STATUSES.get(status, status)
        revisions = revisions.filter(status=db_status)
    for revision in revisions.iterator():
        yield _row('place_revision', 'place', revision.pk, revision.payload.get('name_az') or revision.place.name,
                   REVISION_STATUSES.get(revision.status, revision.status), revision, now,
                   reverse('admin:volunteer_moderation_detail', args=['content', revision.pk]))


def _review_sources(heads, revisions, status):
    # A pending edit keeps the previous approved text on its public head. Older
    # superseded pending submissions are history; only the pointer is actionable.
    active = Q(status='pending', pk=F('review__candidate_revision_id'))
    if status != 'pending':
        latest_decision = (revisions.objects.filter(review_id=OuterRef('review_id'), status__in=('approved', 'rejected'))
            .order_by('-created_at', '-pk').values('pk')[:1])
        active |= ~Q(review__candidate_revision__status='pending') & Q(pk=Subquery(latest_decision))
    # A backfilled baseline is a copy of the original record. If no newer
    # submission exists, an administrator may have corrected that record's
    # dates since import. The version is authoritative once real edits exist.
    edits = revisions.objects.filter(review_id=OuterRef('review_id'), is_baseline=False)
    versions = (revisions.objects.filter(active, review__is_current=True)
        .annotate(has_edits=Exists(edits)).select_related('review')
        .only('status', 'text', 'created_at', 'submitted_at', 'moderated_at', 'is_baseline',
              'review__status', 'review__text', 'review__created_at', 'review__updated_at',
              'review__submitted_at', 'review__moderated_at'))
    legacy = heads.objects.filter(is_current=True, revisions__isnull=True)
    if status != 'all':
        versions = versions.filter(status=status)
        legacy = legacy.filter(status=status)
    for version in versions.iterator():
        if version.is_baseline and not version.has_edits and version.review.status == version.status:
            yield version.review_id, version.review
        else:
            yield version.review_id, version
    # Old imports can have no version history. Reading the panel must not create it.
    for head in legacy.iterator():
        yield head.pk, head


def _reviews(kinds, status, selected, now):
    if status == 'needs_changes':
        return
    if 'site_review' in kinds and matches_queue_type('site_review', 'review', selected):
        site_reviews = SiteReview.objects.all()
        if status != 'all':
            site_reviews = site_reviews.filter(status=status)
        for review in site_reviews.iterator():
            yield _row('site_review', 'review', review.pk, review.text[:100] or f'#{review.pk}', review.status,
                       review, now, reverse('admin:catalog_sitereview_change', args=[review.pk]))
    for kind, (heads, revisions) in TYPED_REVIEWS.items():
        if kind not in kinds or not matches_queue_type(kind, 'review', selected):
            continue
        for head_id, source in _review_sources(heads, revisions, status):
            yield _row(kind, 'review', head_id, source.text[:100] or f'#{head_id}', source.status, source, now,
                       reverse(f'admin:catalog_{heads._meta.model_name}_workflow', args=[head_id]))


def _proposals(status, selected, now):
    kinds = [kind for kind in PROPOSAL_TYPES if matches_queue_type(kind + '_revision', kind, selected)]
    if not kinds:
        return
    # Exactly one target per revision (publication_revision_one_target). Read
    # just its identity and label; the comparison belongs to the detail page.
    revisions = VolunteerPlaceRevision.objects.filter(place__isnull=True)
    if len(kinds) == 1:
        revisions = revisions.filter(**{kinds[0] + '__isnull': False})
    if status == 'all':
        revisions = revisions.exclude(status='draft')
    else:
        revisions = revisions.filter(status=STORED_REVISION_STATUSES.get(status, status))
    labels = [f'{kind}__name_{lang}' for kind in kinds for lang in ('az', 'ru', 'en')]
    revisions = revisions.select_related(*kinds).only('status', 'payload', 'created_at', 'updated_at',
        'submitted_at', 'needs_changes_at', 'moderated_at', *labels)
    for revision in revisions.iterator():
        kind = next(kind for kind in kinds if getattr(revision, kind + '_id') is not None)
        target = getattr(revision, kind)
        name = revision.payload.get('name_az') or target.name_az or target.name_ru or target.name_en or f'#{target.pk}'
        yield _row(kind + '_revision', kind, revision.pk, name, REVISION_STATUSES.get(revision.status, revision.status),
                   revision, now, reverse('admin:volunteer_moderation_detail', args=['content', revision.pk]))


def _affiliations(status, now):
    if status == 'needs_changes':
        return
    requests = OrganizationPlaceRequest.objects.filter(relationship_kind='informational').select_related(
        'place', 'organization').only('status', 'created_at', 'decided_at', 'place__name',
        'place__name_az', 'place__name_ru', 'place__name_en',
        'organization__name_az', 'organization__name_ru', 'organization__name_en')
    if status != 'all':
        requests = requests.filter(status=status)
    for item in requests.iterator():
        yield _row('affiliation', 'affiliation', item.pk, f'{item.place} → {item.organization}', item.status,
                   item, now, reverse('admin:volunteer_moderation_detail', args=['affiliation', item.pk]))


def queue_rows(user, params, *, now):
    if not user.is_authenticated or not user.pk:
        return []
    # has_perm() caches grants on the actor instance. Recheck the stored grants
    # when returning queue contents, just as the proposal detail page does.
    actor = get_user_model().objects.filter(pk=user.pk, is_active=True, is_staff=True).only(
        'is_active', 'is_staff', 'is_superuser').first()
    if actor is None:
        return []
    kinds = allowed_kinds(actor)
    status = params.get('status', 'pending')
    if status not in {'pending', 'needs_changes', 'approved', 'rejected', 'all'}:
        status = 'pending'
    selected = params.get('type', '')
    rows = list(_places(status, selected, now)) if 'place' in kinds else []
    rows.extend(_reviews(kinds, status, selected, now))
    if 'place_revision' in kinds:
        rows.extend(_proposals(status, selected, now))
    if 'affiliation' in kinds and matches_queue_type('affiliation', 'affiliation', selected):
        rows.extend(_affiliations(status, now))
    result = []
    for row in rows:
        sla = row['sla']
        if params.get('sla_status') and params['sla_status'] != sla.status:
            continue
        if not matches_submission_date(row['submitted_at'], params):
            continue
        row['age_hours'] = round(sla.elapsed_seconds / 3600, 1)
        row['remaining_hours'] = round(sla.remaining_seconds / 3600, 1) if sla.remaining_seconds is not None else None
        result.append(row)
    return sorted(result, key=lambda row: (row['submitted_at'], row['kind'], row['id']))
