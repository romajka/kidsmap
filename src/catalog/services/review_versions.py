"""Atomic typed review candidates and visible approved projections (Task33 D07)."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone


class ReviewConflict(Exception):
    pass


class ReviewCooldown(Exception):
    def __init__(self, next_allowed_at):
        self.next_allowed_at = next_allowed_at
        super().__init__('Review cooldown active')


def save_legacy_source(head, save):
    """Retain trusted legacy inserts as distinct sources, elect one known-account head."""
    if getattr(head, '_version_service', False):
        return save()
    kind, (targets, heads, _, _) = type_for_head(head)
    with transaction.atomic():
        targets.objects.select_for_update().get(pk=getattr(head, kind + '_id'))
        if head.pk:
            previous = heads.objects.select_for_update().get(pk=head.pk)
            ensure_baseline(previous)
            previous.refresh_from_db()
            result = save()
            changed = any(getattr(head, field) != getattr(previous, field) for field in
                ('status', 'text', 'rating', 'author_name', 'is_anonymous', 'contains_profanity', 'rejection_reason'))
            if not changed:
                return result
            revisions = review_types()[kind][2]
            candidate = previous.candidate_revision if previous.candidate_revision_id else None
            if (candidate and candidate.status == 'pending' and head.status in {'approved', 'rejected'}
                    and candidate.text == head.text and candidate.rating == head.rating):
                revisions.objects.filter(pk=candidate.pk).update(status=head.status, moderated_at=head.moderated_at,
                    moderated_by_id=head.moderated_by_id, rejection_reason=head.rejection_reason,
                    source_is_approved=head.is_approved)
                revision_id = candidate.pk
            else:
                values = baseline_values(head)
                values.update(created_at=timezone.now(), is_baseline=False)
                revision_id = revisions.objects.create(review_id=head.pk, **values).pk
            if head.status == 'approved':
                patch = {'current_revision_id': revision_id, 'candidate_revision_id': None}
            elif previous.current_revision_id:
                current = previous.current_revision
                patch = {key: getattr(current, key) for key in
                    ('rating', 'text', 'author_name', 'is_anonymous', 'contains_profanity', 'submitted_at', 'moderated_at', 'moderated_by_id', 'rejection_reason')}
                patch.update(status='approved', is_approved=True,
                    candidate_revision_id=revision_id if head.status == 'pending' else None)
            else:
                patch = {'candidate_revision_id': revision_id if head.status == 'pending' else None}
            heads.objects.filter(pk=head.pk).update(**patch)
            head.refresh_from_db()
            return result
        head.is_current = False
        result = save()
        ensure_baseline(head)
        rows = list(heads.objects.filter(**{kind + '_id': getattr(head, kind + '_id'), 'user_id': head.user_id}).filter(Q(is_current=True) | Q(archive_head__isnull=True))) if head.user_id else [head]
        current = max(rows, key=lambda s: (s.status == 'approved' and s.is_approved, s.moderated_at or s.created_at, s.pk))
        heads.objects.filter(pk__in=[s.pk for s in rows if s.pk != current.pk]).update(is_current=False, archive_head=current)
        heads.objects.filter(pk=current.pk).update(is_current=True, archive_head=None)
        head.refresh_from_db()
        return result


def review_types():
    from catalog import models as m
    return {
        'place': (m.Place, m.PlaceReview, m.PlaceReviewRevision, m.PlaceReviewReaction),
        'specialist': (m.Specialist, m.SpecialistReview, m.SpecialistReviewRevision, m.SpecialistReviewReaction),
        'activity': (m.Activity, m.ActivityReview, m.ActivityReviewRevision, m.ActivityReviewReaction),
        'event': (m.Event, m.EventReview, m.EventReviewRevision, m.EventReviewReaction),
    }


def type_for_head(head):
    for kind, types in review_types().items():
        if isinstance(head, types[1]):
            return kind, types
    raise ValueError('Unsupported review type')


def baseline_values(source):
    return {key: getattr(source, key, default) for key, default in {
        'author_name': '', 'is_anonymous': False, 'rating': 5, 'text': '',
        'contains_profanity': False, 'status': 'pending', 'submitted_at': None,
        'moderated_at': None, 'moderated_by_id': None, 'rejection_reason': '',
        'created_at': timezone.now(),
        'source_is_approved': getattr(source, 'is_approved', False),
    }.items()}


def ensure_baseline(head):
    """Compatibility for new rows written by legacy scripts/tests, without editing history."""
    kind, (_, model, revisions, reactions) = type_for_head(head)
    with transaction.atomic():
        locked = model.objects.select_for_update().get(pk=head.pk)
        if locked.revisions.exists():
            return locked.revisions.order_by('created_at', 'pk').first()
        revision = locked.revisions.filter(is_baseline=True).first()
        if revision is None:
            revision = revisions.objects.create(review=locked, is_baseline=True, **baseline_values(locked))
        patch = {}
        if revision.status == 'approved' and locked.current_revision_id is None:
            patch['current_revision_id'] = revision.pk
        elif locked.current_revision_id is None and locked.candidate_revision_id is None:
            patch['candidate_revision_id'] = revision.pk
        if patch:
            model.objects.filter(pk=locked.pk).update(**patch)
            for key, value in patch.items():
                setattr(head, key, value)
        reactions.objects.filter(review=locked, revision__isnull=True).update(revision=revision)
        return revision


def normalize_reviews(model):
    """Local compatibility normalization; migration uses frozen historical models separately."""
    kind = next(k for k, types in review_types().items() if types[1] is model)
    for target_id in model.objects.values_list(kind + '_id', flat=True).distinct():
        target_model = review_types()[kind][0]
        with transaction.atomic():
            target_model.objects.select_for_update().get(pk=target_id)
            sources = list(model.objects.filter(**{kind + '_id': target_id}).order_by('pk'))
            groups = {}
            for source in sources:
                ensure_baseline(source)
                # Preserve normalized archive identity even after user deletion.
                if not source.is_current and source.archive_head_id:
                    continue
                key = ('user', source.user_id) if source.user_id else ('source', source.pk)
                groups.setdefault(key, []).append(source)
            for group in groups.values():
                head = max(group, key=lambda s: (s.status == 'approved' and s.is_approved, s.moderated_at or s.created_at, s.pk))
                others = [s.pk for s in group if s.pk != head.pk]
                model.objects.filter(pk__in=others).update(is_current=False, archive_head=head)
                model.objects.filter(pk=head.pk).update(is_current=True, archive_head=None)


def submit_review(*, target, user, rating, text, author_name='', contains_profanity=False, expected_revision_id=None, enforce_cooldown=False):
    if not getattr(user, 'is_authenticated', False) or not user.is_active:
        raise PermissionError('Active account required')
    if not 1 <= int(rating) <= 5 or not text.strip() or len(text) > 5000 or len(author_name) > 80:
        raise ValidationError('Invalid review content')
    if expected_revision_id is not None:
        try:
            expected_revision_id = int(expected_revision_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError('Invalid review version') from exc
        if expected_revision_id <= 0:
            raise ValidationError('Invalid review version')
    selected = next(((k, t) for k, t in review_types().items() if isinstance(target, t[0])), None)
    if selected is None:
        raise ValueError('Unsupported review target')
    kind, (target_model, heads, revisions, _) = selected
    with transaction.atomic():
        # Target lock serializes first submit before a head exists and avoids deadlock inversion.
        target_model.objects.select_for_update().get(pk=target.pk)
        if not get_user_model().objects.filter(pk=user.pk, is_active=True).exists():
            raise PermissionError('Active account required')
        head = heads.objects.select_for_update().filter(**{kind: target, 'user': user, 'is_current': True}).first()
        if head:
            ensure_baseline(head)
        if expected_revision_id is not None and (not head or int(expected_revision_id) != (head.candidate_revision_id or head.current_revision_id)):
            raise ReviewConflict('Review changed; reload before submitting')
        now = timezone.now()
        if enforce_cooldown:
            from catalog.services.place_review_submission import cooldown_seconds
            latest = head.revisions.order_by('-created_at', '-pk').first() if head else None
            if latest and latest.created_at + timedelta(seconds=cooldown_seconds()) > now:
                raise ReviewCooldown(latest.created_at + timedelta(seconds=cooldown_seconds()))
        if head is None:
            head = heads(**{kind: target, 'user': user, 'rating': rating, 'text': text, 'author_name': author_name, 'contains_profanity': contains_profanity, 'status': 'pending', 'is_approved': False, 'submitted_at': now})
            head._version_service = True
            head.save()
        revision = revisions.objects.create(review=head, rating=rating, text=text, author_name=author_name,
            contains_profanity=contains_profanity, status='pending', submitted_at=now, created_at=now)
        patch = {'candidate_revision_id': revision.pk}
        if head.current_revision_id is None:
            patch.update(rating=rating, text=text, author_name=author_name, contains_profanity=contains_profanity,
                status='pending', is_approved=False, submitted_at=now, moderated_at=None, moderated_by_id=None, rejection_reason='')
        heads.objects.filter(pk=head.pk).update(**patch)
        head.refresh_from_db()
        return head, revision


def moderate_candidate(*, head, revision_id, actor, approve, reason=''):
    kind, (targets, heads, revisions, _) = type_for_head(head)
    if not actor.is_active or not actor.is_staff or not actor.has_perm('catalog.change_' + heads._meta.model_name):
        raise PermissionError('KidsMap reviewer permission required')
    with transaction.atomic():
        targets.objects.select_for_update().get(pk=getattr(head, kind + '_id'))
        fresh_actor = get_user_model().objects.get(pk=actor.pk)
        if not fresh_actor.is_active or not fresh_actor.is_staff or not fresh_actor.has_perm('catalog.change_' + heads._meta.model_name):
            raise PermissionError('KidsMap reviewer permission required')
        locked = heads.objects.select_for_update().get(pk=head.pk)
        if not locked.is_current or locked.candidate_revision_id != int(revision_id):
            raise ReviewConflict('Candidate was replaced or already decided')
        candidate = revisions.objects.get(pk=revision_id, review=locked)
        if candidate.status != 'pending':
            raise ReviewConflict('Candidate already decided')
        candidate.status = 'approved' if approve else 'rejected'
        candidate.moderated_at = timezone.now()
        candidate.moderated_by = fresh_actor
        candidate.rejection_reason = '' if approve else reason
        candidate.save(update_fields=['status', 'moderated_at', 'moderated_by', 'rejection_reason'])
        patch = {'candidate_revision_id': None}
        if approve or locked.current_revision_id is None:
            patch.update({key: getattr(candidate, key) for key in ['rating', 'text', 'author_name', 'is_anonymous', 'contains_profanity', 'status', 'submitted_at', 'moderated_at', 'moderated_by_id', 'rejection_reason']})
            patch['is_approved'] = approve
        if approve:
            patch['current_revision_id'] = candidate.pk
        heads.objects.filter(pk=locked.pk).update(**patch)
        locked.refresh_from_db()
        refresh_reactions(locked)
        target = getattr(locked, kind)
        if hasattr(target, 'refresh_rating_stats'):
            target.refresh_rating_stats()
        return candidate


def refresh_reactions(head):
    stats = head.reactions.filter(revision_id=head.current_revision_id).aggregate(likes=Count('pk', filter=Q(value=1)), dislikes=Count('pk', filter=Q(value=-1)))
    type(head).objects.filter(pk=head.pk).update(likes_count=stats['likes'] or 0, dislikes_count=stats['dislikes'] or 0)


def current_reviews(queryset):
    if hasattr(queryset.model, 'is_current'):
        return queryset.filter(is_current=True)
    return queryset


def business_can_respond(*, user, head, action='reply'):
    from catalog.services.business_team import has_action
    kind, _ = type_for_head(head)
    target = getattr(head, kind)
    if kind in {'place', 'activity'}:
        place = target if kind == 'place' else target.place
        return has_action(user=user, target=place, action='place.reviews.' + action)
    if kind == 'specialist':
        from catalog.services.specialist_documents import is_person
        return is_person(user, target)
    if kind == 'event':
        from catalog.services.event_domain import can_manage_event
        return can_manage_event(user, target)
    return False


def respond_to_review(*, head, actor, revision_id, kind, text):
    if kind not in {'reply', 'report'} or not text.strip() or len(text) > 5000:
        raise ValidationError('Invalid review response')
    if not actor.is_authenticated or not actor.is_active or not business_can_respond(user=actor, head=head, action=kind):
        raise PermissionError('Target business access required')
    target_kind, (targets, heads, _, _) = type_for_head(head)
    with transaction.atomic():
        if target_kind == 'event':
            from catalog.services.event_domain import lock_event_for_response
            lock_event_for_response(actor=actor, event_id=head.event_id)
        else:
            targets.objects.select_for_update().get(pk=getattr(head, target_kind + '_id'))
        locked = heads.objects.select_for_update().get(pk=head.pk)
        if not business_can_respond(user=actor, head=locked, action=kind):
            raise PermissionError('Target business access revoked')
        if not locked.is_current or not locked.is_approved or str(locked.current_revision_id) != str(revision_id):
            raise ReviewConflict('Visible review changed')
        from catalog import models as m
        response_model = getattr(m, heads.__name__ + 'Response')
        return response_model.objects.create(revision_id=revision_id, actor=actor, kind=kind, text=text.strip())


def rating_summary(target):
    """Each typed target's approved current contributions; Organization has no score."""
    from django.db.models import Avg
    from catalog.services.content_quality import public_review_queryset
    selected = next(((k, types) for k, types in review_types().items() if isinstance(target, types[0])), None)
    if not selected:
        return None
    kind, types = selected
    stats = public_review_queryset(types[1].objects.filter(**{kind: target})).aggregate(average=Avg('rating'), count=Count('pk'))
    return {'average': float(stats['average'] or 0), 'count': stats['count']}
