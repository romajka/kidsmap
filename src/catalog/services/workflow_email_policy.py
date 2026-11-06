"""Freshness, current rights and content of service emails, independent of SMTP."""
import hashlib
from collections import Counter
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db.models import Max, Q
from django.conf import settings
from django.urls import reverse

from catalog.models import WorkflowNotification

CRITICAL = frozenset({'ownership_transfer', 'access_disabled'})
DIGEST = frozenset({'team_invitation', 'join_confirmation', 'moderation_decision',
                    'team_invitation_decision', 'join_approved', 'affiliation_decision',
                    'affiliation_detached'})
COLLECT_FOR = timedelta(minutes=15)
COLLECT_MAX_WAIT = timedelta(hours=1)
COOLDOWN = timedelta(minutes=30)
MAX_AGE = timedelta(hours=24)
CRITICAL_MAX_AGE = timedelta(days=7)


def address_key(address):
    return hashlib.sha256(address.strip().lower().encode()).hexdigest()


def ensure_recipient_state(address):
    from catalog.models import EmailOutbox, WorkflowEmailRecipientState
    def latest_sent():
        return (EmailOutbox.objects.filter(recipient_email__iexact=address, status='sent')
                .exclude(notification__event_kind__in=CRITICAL).aggregate(last=Max('sent_at'))['last'])
    return WorkflowEmailRecipientState.objects.get_or_create(address_key=address_key(address),
        defaults={'last_digest_sent_at': latest_sent})[0]


def _moderation_current(item):
    from catalog.models import Specialist, VolunteerPlaceRevision
    from catalog.services import publication
    context = item.event_context or {}
    decision = context.get('decision')
    if item.entity_type == 'volunteer_revision':
        revision = VolunteerPlaceRevision.objects.filter(pk=item.entity_id).first()
        expected = {'approved': 'approved', 'needs_changes': 'rejected', 'rejected': 'declined'}.get(decision)
        kind = context.get('target_type')
        if (not revision or not expected or revision.version != item.entity_version
                or revision.status != expected or revision.author_id != item.recipient_user_id
                or kind not in publication.TARGETS
                or getattr(revision, kind + '_id') != context.get('target_id')):
            return False
        target = getattr(revision, kind)
        if (getattr(target, 'deleted_at', None) or getattr(target, 'archived_at', None)):
            return False
        try:
            publication.authorize(item.recipient_user, target, kind)
        except PermissionDenied:
            return False
        return True
    if item.entity_type == 'specialist':
        person = Specialist.objects.filter(pk=item.entity_id).first()
        expected = {'approved': 'published', 'needs_changes': 'draft', 'rejected': 'rejected'}.get(decision)
        return bool(person and expected and person.status == expected
                    and (decision != 'approved' or person.is_active)
                    and item.recipient_user_id in {person.created_by_id, person.verified_person_user_id}
                    and item.recipient_user_id is not None)
    return False


def _business_event_current(item):
    from catalog.models import (Organization, Place, OwnerTeamMembership, OrganizationGrant,
                                OwnerTeamInvitation, OrganizationTeamInvitation, OrganizationPlaceRequest)
    context = item.event_context or {}
    user_id = item.recipient_user_id
    if item.event_kind == 'ownership_transfer':
        model = {'place': Place, 'organization': Organization}.get(item.entity_type)
        target = model.objects.filter(pk=item.entity_id).first() if model else None
        return bool(target and target.ownership_version == item.entity_version
                    and target.owner_id == context.get('new_owner_id')
                    and user_id in {context.get('previous_owner_id'), context.get('new_owner_id')}
                    and user_id is not None)
    if item.event_kind == 'access_disabled':
        model = {'place_team_grant': OwnerTeamMembership, 'organization_team_grant': OrganizationGrant}.get(item.entity_type)
        grant = model.objects.filter(pk=item.entity_id).first() if model else None
        return bool(grant and grant.member_id == user_id and grant.version == item.entity_version
                    and not grant.is_active)
    if item.event_kind == 'team_invitation_decision':
        model = {'place_team_invitation': OwnerTeamInvitation,
                 'organization_team_invitation': OrganizationTeamInvitation}.get(item.entity_type)
        invite = model.objects.filter(pk=item.entity_id).first() if model else None
        if not invite or invite.status not in {'ACCEPTED', 'REJECTED'} or invite.owner_id != user_id:
            return False
        parent = invite.place if item.entity_type == 'place_team_invitation' else invite.organization
        if (not parent or (parent.owner_id or getattr(parent, 'created_by_id', None)) != user_id
                or parent.ownership_version != invite.base_ownership_version
                or getattr(parent, 'archived_at', None) or getattr(parent, 'deleted_at', None)):
            return False
        field = 'place' if item.entity_type == 'place_team_invitation' else 'organization'
        if model.objects.filter(**{field: parent}, email__iexact=invite.email, pk__gt=invite.pk).exists():
            return False
        if invite.status == 'ACCEPTED':
            grant_model = OwnerTeamMembership if field == 'place' else OrganizationGrant
            return grant_model.objects.filter(**{field: parent}, member_id=invite.invited_user_id,
                owner_id=user_id, is_active=True, version=(invite.base_grant_version or 0) + 1).exists()
        return True
    if item.event_kind in {'join_approved', 'affiliation_decision'}:
        request = OrganizationPlaceRequest.objects.select_related('place', 'organization').filter(pk=item.entity_id).first()
        if not request:
            return False
        if OrganizationPlaceRequest.objects.filter(place_id=request.place_id,
                organization_id=request.organization_id, pk__gt=request.pk).exists():
            return False
        if item.event_kind == 'affiliation_decision':
            return (request.requested_by_id == user_id and request.status in {'canceled', 'rejected'}
                    and request.status == context.get('decision'))
        return (request.status == 'approved' and request.place.organization_id == request.organization_id
                and request.place.owner_id == request.base_place_owner_id
                and request.organization.owner_id == request.base_organization_owner_id
                and request.place.ownership_version == request.base_place_ownership_version
                and request.organization.ownership_version == request.base_organization_ownership_version
                and user_id in {request.place.owner_id, request.organization.owner_id, request.requested_by_id})
    if item.event_kind == 'affiliation_detached':
        place = Place.objects.filter(pk=item.entity_id, deleted_at__isnull=True).first()
        return bool(place and place.organization_id is None and place.content_version == item.entity_version
                    and user_id in context.get('recipient_ids', []))
    return False


def suppression_reason(item, address, now, cutoff):
    """No mutation: used by delivery and preview. Unrecognized events fail closed."""
    from catalog.services.workflow_notifications import _delivery_allowed
    if item.created_at < cutoff:
        return 'before_activation'
    critical = item.event_kind in CRITICAL
    if item.created_at < now - (CRITICAL_MAX_AGE if critical else MAX_AGE):
        return 'expired'
    if item.event_kind not in CRITICAL | DIGEST:
        return 'unsupported_event'
    if not _delivery_allowed(item, address, now):
        return 'stale_access'
    context = item.event_context or {}
    actor_id = context.get('actor_id')
    if not critical and item.recipient_user_id and item.recipient_user.is_staff:
        if actor_id is None and item.entity_type == 'volunteer_revision':
            from catalog.models import VolunteerPlaceRevision
            actor_id = VolunteerPlaceRevision.objects.filter(pk=item.entity_id).values_list('reviewed_by_id', flat=True).first()
        if actor_id == item.recipient_user_id:
            return 'self_staff_action'
    if item.event_kind == 'moderation_decision':
        newer = WorkflowNotification.objects.filter(event_kind=item.event_kind,
            entity_type=item.entity_type, entity_id=item.entity_id, recipient_email__iexact=address).filter(
                Q(entity_version__gt=item.entity_version) | Q(entity_version=item.entity_version, pk__gt=item.pk))
        if newer.exists() or not _moderation_current(item):
            return 'superseded'
    elif item.event_kind not in {'team_invitation', 'join_confirmation'} and not _business_event_current(item):
        return 'stale_event'
    return ''


def digest_ready(items, state, now):
    first = min(item.created_at for item in items)
    last_created = max(item.created_at for item in items)
    last = state.last_digest_sent_at if state else None
    collect_until = min(last_created + COLLECT_FOR, first + COLLECT_MAX_WAIT)
    return now >= collect_until and (last is None or now >= last + COOLDOWN)


_DECISIONS = {'approved': 'Одобрено', 'needs_changes': 'Нужны исправления', 'rejected': 'Отклонено'}
_EVENTS = {'team_invitation': 'Приглашение в команду — примите или отклоните в кабинете',
           'join_confirmation': 'Связь места с организацией — проверьте и подтвердите в кабинете',
           'join_approved': 'Связь места с организацией подтверждена',
           'affiliation_detached': 'Связь места с организацией прекращена',
           'affiliation_decision': 'Заявка на связь с организацией требует внимания',
           'team_invitation_decision': 'Получен ответ на приглашение'}


def _label(item):
    decision = item.event_context.get('decision')
    if item.event_kind == 'moderation_decision':
        return _DECISIONS.get(decision, 'Решение модерации')
    if item.event_kind == 'team_invitation_decision':
        return 'Приглашение принято' if decision == 'accepted' else 'Приглашение отклонено'
    if item.event_kind == 'affiliation_decision':
        return 'Заявка на связь отклонена' if decision == 'rejected' else 'Заявка на связь возвращена на доработку'
    return _EVENTS.get(item.event_kind, 'Изменение в кабинете')


def email_content(items):
    """Private moderator text stays in the authenticated inbox, including digests."""
    from catalog.services.workflow_notifications import _email_content
    if len(items) == 1:
        item = items[0]
        if item.entity_type == 'specialist' and item.event_kind == 'moderation_decision':
            return _email_content(item)
        if item.event_kind in CRITICAL:
            title = 'Изменился владелец' if item.event_kind == 'ownership_transfer' else 'Доступ сотрудника отключён'
            return 'KidsMap: ' + title, title + '.\nЭто служебное уведомление. Проверьте текущие права в кабинете:\n' + inbox_url()
    actions = sum(item.event_kind in {'team_invitation', 'join_confirmation', 'affiliation_decision'}
                  or item.event_context.get('decision') in {'needs_changes', 'rejected'} for item in items)
    summary = Counter(_label(item) for item in items)
    body = [f'Событий: {len(items)}. Требуют внимания: {actions}.', '']
    body += [f'{title}: {count}' for title, count in summary.items()]
    ordered = sorted(items, key=lambda item: item.event_context.get('decision') not in {'needs_changes', 'rejected'})
    body += ['', 'Последние решения:']
    for item in ordered[:10]:
        context = item.event_context or {}
        titles = context.get('titles') or {}
        name = ' '.join(str(titles.get('ru') or titles.get('az') or '').split())[:120]
        label = _label(item)
        body.append(f'• {label}' + (f' — {name}' if name else ''))
    body += ['', 'Откройте кабинет: там комментарии, текущий статус и необходимые действия.', inbox_url()]
    return f'KidsMap: сводка — {len(items)} событий', '\n'.join(body)


def inbox_url():
    return (settings.PUBLIC_BASE_URL or 'http://localhost') + reverse('account_notifications')
