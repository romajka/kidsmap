"""Reviewer-only read model over the existing publication and affiliation queues."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from catalog.models import Activity, OrganizationPlaceRequest, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.business_team import platform_has_action
from catalog.services.moderation_sla import calculate_sla
from catalog.services.permanent_place_rules import copy as t

ENTITIES = frozenset((*publication.TARGETS, 'affiliation'))
STATUSES = frozenset({'all', 'draft', 'pending', 'rejected', 'declined', 'approved', 'canceled'})


def kind_label(kind):
    return {
        'place': t('Место', 'Məkan', 'Place'),
        'organization': t('Организация', 'Təşkilat', 'Organization'),
        'program': t('Программа', 'Proqram', 'Program'),
        'activity': t('Занятие', 'Məşğələ', 'Activity'),
        'offering_group': t('Группа', 'Qrup', 'Group'),
        'affiliation': t('Информационная связь', 'Məlumat əlaqəsi', 'Informational link'),
    }[kind]

def status_label(status):
    return {
        'draft': t('Черновик', 'Qaralama', 'Draft'),
        'pending': t('На проверке', 'Yoxlamada', 'Pending'),
        'rejected': t('На доработке', 'Düzəlişdə', 'Needs changes'),
        'declined': t('Отклонено', 'Rədd edilib', 'Rejected'),
        'approved': t('Одобрено', 'Təsdiqlənib', 'Approved'),
        'canceled': t('Возвращено', 'Geri qaytarılıb', 'Returned'),
    }.get(status, status)

def mode_label(mode):
    return t('Новое', 'Yeni', 'New') if mode == 'new' else t('Правка', 'Düzəliş', 'Edit')

def sla_label(status):
    return {
        'fresh': t('В срок', 'Vaxtında', 'On time'),
        'warning': t('Близок срок', 'Müddət yaxınlaşır', 'Due soon'),
        'critical': t('Критический срок', 'Kritik müddət', 'Critical'),
        'breached': t('Срок истёк', 'Müddət bitib', 'Overdue'),
        'paused': t('Пауза', 'Dayandırılıb', 'Paused'),
        'completed': t('Рассмотрено', 'Baxılıb', 'Completed'),
        'unknown': t('Без срока', 'Müddət yoxdur', 'No deadline'),
    }.get(status, status)

def field_label(target, key):
    if key.startswith('name_'):
        return f"{t('Название', 'Ad', 'Name')} ({key[-2:].upper()})"
    if key.startswith('description_'):
        return f"{t('Описание', 'Təsvir', 'Description')} ({key[-2:].upper()})"
    try:
        return str(target._meta.get_field(key).verbose_name)
    except Exception:
        return key.replace('_', ' ')


def reviewer_scopes(actor):
    from catalog.services.staff_roles import is_volunteer
    actor = publication.fresh_actor(actor)
    if not actor.is_staff or is_volunteer(actor):
        raise PermissionDenied
    content = platform_has_action(user=actor, action='place.publish')
    affiliation = actor.is_superuser or actor.has_perm('catalog.change_placeownershiprequest')
    if not (content or affiliation):
        raise PermissionDenied
    return actor, content, affiliation

def require_reviewer(actor):
    return reviewer_scopes(actor)[0]


def _target(revision):
    kind, pk = publication._kind(revision)
    return kind, getattr(revision, kind)


def _branches(kind, target):
    if kind == 'program':
        return list(Activity.objects.filter(program=target, archived_at__isnull=True).select_related('place').order_by('place_id').values_list('place_id', flat=True).distinct())
    if kind == 'organization':
        return list(target.places.filter(deleted_at__isnull=True).order_by('pk').values_list('pk', flat=True))
    if kind == 'activity':
        return [target.place_id]
    if kind == 'offering_group':
        return [target.activity.place_id]
    return [target.pk]


def _revision_row(revision, now):
    kind, target = _target(revision)
    current = publication.snapshot(target, kind)
    conflict = (revision.schema_version != publication.SCHEMA_VERSION
        or revision.dependencies != publication.dependencies(target, kind)
        or any(current.get(key) != revision.base_snapshot.get(key) for key in revision.changed_fields))
    status = revision.status
    submitted = revision.submitted_at or revision.created_at
    return {'source': 'content', 'id': revision.pk, 'kind': kind, 'status': status,
        'author_id': revision.author_id, 'author': revision.author,
        'organization_id': target.pk if kind == 'organization' else target.organization_id if kind in {'place', 'program'} else target.place.organization_id if kind == 'activity' else target.activity.place.organization_id,
        'place_ids': _branches(kind, target), 'target_id': target.pk,
        'name': revision.payload.get('name_az') or getattr(target, 'name_az', '') or getattr(target, 'name', '') or f'#{target.pk}',
        'new_or_edit': 'new' if getattr(target, 'status', 'draft') != 'published' else 'edit',
        'submitted_at': submitted, 'version': revision.version, 'conflict': conflict,
        'current': current, 'candidate': {**current, **revision.payload},
        'changes': [(field_label(target, key), current.get(key), revision.payload.get(key)) for key in revision.changed_fields],
        'affected_branches': _branches(kind, target),
        'sla': calculate_sla(kind, submitted, now=now,
            paused_at=revision.needs_changes_at if status == 'rejected' else None,
            completed_at=revision.moderated_at if status in {'approved', 'declined'} else None),
        'revision': revision}


def _affiliation_row(item, now):
    submitted = item.created_at
    return {'source': 'affiliation', 'id': item.pk, 'kind': 'affiliation', 'status': item.status,
        'author_id': item.requested_by_id, 'author': item.requested_by,
        'organization_id': item.organization_id, 'place_ids': [item.place_id],
        'target_id': item.place_id, 'name': f"{item.place} → {item.organization.name_az or item.organization.name_ru or item.organization.name_en or ('#' + str(item.organization_id))}",
        'new_or_edit': 'new' if item.place.organization_id is None else 'edit',
        'submitted_at': submitted, 'version': item.base_place_content_version,
        'conflict': not (item.base_place_ownership_version == item.place.ownership_version
            and item.base_organization_ownership_version == item.organization.ownership_version
            and item.base_place_owner_id == item.place.owner_id
            and item.base_organization_owner_id == item.organization.owner_id
            and item.base_place_content_version == item.place.content_version),
        'current': {'organization_id': item.place.organization_id},
        'candidate': {'organization_id': item.organization_id, 'relationship_kind': 'informational'},
        'changes': [(t('Организация', 'Təşkilat', 'Organization'), item.place.organization_id, item.organization_id)],
        'affected_branches': [item.place_id],
        'sla': calculate_sla('affiliation', submitted, now=now,
            completed_at=item.decided_at if item.status != 'pending' else None), 'request': item}


def query(actor, params, *, now=None):
    actor, can_content, can_affiliation = reviewer_scopes(actor)
    now = now or timezone.now()
    entity = params.get('entity', '')
    status = params.get('status', 'pending')
    new_or_edit = params.get('new_or_edit', '')
    if entity and entity not in ENTITIES or status not in STATUSES or new_or_edit not in {'', 'new', 'edit'}:
        raise ValidationError('Unknown moderation filter.')
    rows = []
    if can_content and entity != 'affiliation':
        revisions = VolunteerPlaceRevision.objects.select_related('author', 'place', 'organization', 'program', 'activity__place', 'offering_group__activity__place')
        for revision in revisions:
            # Candidate visibility survives author role changes or deactivation.
            row = _revision_row(revision, now)
            if entity and row['kind'] != entity:
                continue
            rows.append(row)
    if can_affiliation and (not entity or entity == 'affiliation'):
        requests = OrganizationPlaceRequest.objects.filter(relationship_kind='informational').select_related('requested_by', 'place', 'organization')
        for item in requests:
            rows.append(_affiliation_row(item, now))
    counts = {'all': len(rows), **{key: sum(row['status'] == key for row in rows) for key in STATUSES if key != 'all'}}
    def integer_filter(name):
        value = params.get(name, '')
        if not value:
            return None
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError('Invalid moderation filter.') from exc
        if value < 1:
            raise ValidationError('Invalid moderation filter.')
        return value
    author = integer_filter('author')
    organization = integer_filter('org')
    place = integer_filter('place')
    since, until = params.get('from', ''), params.get('to', '')
    for date in (since, until):
        if date:
            from datetime import date as date_type
            try:
                date_type.fromisoformat(date)
            except (TypeError, ValueError) as exc:
                raise ValidationError('Invalid date filter.') from exc
    rows = [row for row in rows if (status == 'all' or row['status'] == status)
        and (not new_or_edit or row['new_or_edit'] == new_or_edit)
        and (author is None or row['author_id'] == author)
        and (organization is None or row['organization_id'] == organization)
        and (place is None or place in row['place_ids'])
        and (not since or row['submitted_at'].date().isoformat() >= since)
        and (not until or row['submitted_at'].date().isoformat() <= until)]
    for row in rows:
        row['kind_label'] = kind_label(row['kind'])
        row['status_label'] = status_label(row['status'])
        row['mode_label'] = mode_label(row['new_or_edit'])
        row['sla_label'] = sla_label(row['sla'].status)
    return sorted(rows, key=lambda row: (row['submitted_at'], row['source'], row['id'])), counts


def detail(actor, source, row_id):
    if source not in {'content', 'affiliation'}:
        raise ValidationError('Unknown moderation source.')
    rows, _ = query(actor, {'status': 'all'}, now=timezone.now())
    for row in rows:
        if row['source'] == source and row['id'] == row_id:
            return row
    from django.http import Http404
    raise Http404('Moderation item missing.')
