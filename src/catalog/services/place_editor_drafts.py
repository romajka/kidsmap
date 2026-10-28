"""Staff presentation adapters for actor-private drafts; never publication actions."""
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.text import smart_split, unescape_string_literal

from catalog.models import ServerDraft, VolunteerPlaceRevision
from catalog.services import publication, server_drafts
from catalog.services.permanent_place_rules import copy as t
from catalog.services.staff_roles import can_use_volunteer_workspace


def _surface(user, surface):
    if not user.is_authenticated or not user.is_active: raise PermissionDenied
    if surface == 'volunteer':
        if not can_use_volunteer_workspace(user): raise PermissionDenied
    elif surface == 'admin':
        if not user.is_staff or can_use_volunteer_workspace(user): raise PermissionDenied
    else:
        raise ValidationError('Invalid editor surface.')


@transaction.atomic
def config_for(*, user, place=None, surface='admin'):
    # Rendering uses this request's authenticated user and middleware role cache.
    # Every draft API read/write still reloads the actor before authorizing.
    _surface(user, surface)
    target_id = place.pk if place and place.pk else None
    target = server_drafts._target(user, 'place', target_id)
    revision = VolunteerPlaceRevision.objects.filter(place=target).first() if target else None
    return {'actorId': user.pk, 'targetType': 'place', 'targetId': target_id,
        'schemaVersion': publication.SCHEMA_VERSION, 'sourceVersion': target.content_version if target else 0,
        'baseSignature': server_drafts.editor_base_signature(target),
        'candidateVersion': revision.version if revision else 0,
        'fields': sorted((publication.fields_for('place') - {'photo', 'cover_photo', 'gallery'}) | server_drafts.PLACE_EDITOR_DRAFT_FIELDS),
        'collectionUrl': reverse('server_draft_collection'),
        'listUrl': reverse('admin:volunteer_index' if surface == 'volunteer' else 'admin:catalog_place_changelist'),
        'surface': surface}


def working_draft_rows(*, user, surface='admin', query=''):
    _surface(user, surface)
    seen_targets = set()
    language = (get_language() or 'az').split('-')[0]
    terms = [unescape_string_literal(term) if term.startswith(('"', "'")) and term[0] == term[-1]
             else term for term in smart_split(query)]
    for draft in ServerDraft.objects.filter(actor=user, target_type='place', materialized_place__isnull=True).order_by('-saved_at', '-pk').iterator():
        needs_review = False
        try:
            server_drafts.read(user=user, draft_id=draft.pk)
        except server_drafts.DraftConflict:
            needs_review = True  # Keep work visible, but never restore it silently.
        except (PermissionDenied, ValidationError, ServerDraft.DoesNotExist):
            continue
        if draft.target_id:
            if draft.target_id in seen_targets: continue
            seen_targets.add(draft.target_id)
        title = next((str(draft.fields.get(key)).strip() for key in
                      ('name_' + language, 'name_az', 'name_ru', 'name_en') if draft.fields.get(key)), '')
        searchable = [str(draft.fields.get(key) or '').casefold() for key in
                      ('name_az', 'name_ru', 'name_en', 'address', 'phone1', 'phone2', 'phone3',
                       'website', 'instagram')]
        if any(not any(term.casefold() in value for value in searchable) for term in terms): continue
        if surface == 'volunteer':
            url = reverse('admin:volunteer_edit', args=[draft.target_id]) if draft.target_id else reverse('admin:volunteer_add')
        else:
            url = reverse('admin:catalog_place_change', args=[draft.target_id]) if draft.target_id else reverse('admin:catalog_place_add')
        yield {'id': str(draft.pk), 'target_id': draft.target_id,
            'version': draft.version, 'delete_url': reverse('server_draft_detail', args=[draft.pk]),
            'title': title or t('Новое место', 'Yeni məkan', 'New place'),
            'saved_at': draft.saved_at, 'needs_review': needs_review,
            'url': url + '?' + urlencode({'type': 'permanent', 'draft_id': str(draft.pk), 'draft_session': str(draft.pk)})}


def working_drafts_context(*, user, surface='admin', params=None):
    params = params or {}
    rows = list(working_draft_rows(user=user, surface=surface, query=params.get('q', '').strip()[:200]))
    new_rows = [row for row in rows if row['target_id'] is None]
    page = Paginator(new_rows, 12).get_page(params.get('draft_page'))
    def page_url(number):
        values = params.copy()
        values['draft_page'] = number
        return '?' + (values.urlencode() if hasattr(values, 'urlencode') else urlencode(values))
    return {'working_drafts_page': page,
        'working_drafts_previous_url': page_url(page.previous_page_number()) if page.has_previous() else '',
        'working_drafts_next_url': page_url(page.next_page_number()) if page.has_next() else '',
        'working_drafts_by_target': {row['target_id']: row for row in rows if row['target_id']},
        'working_drafts_count': len(rows), 'working_drafts_copy': {
            'title': t('Незавершённые черновики', 'Tamamlanmamış qaralamalar', 'Unfinished drafts'),
            'saved': t('Сохранено', 'Saxlanıldı', 'Saved'),
            'continue': t('Продолжить заполнение черновика', 'Qaralamanı davam etdir', 'Continue editing draft'),
            'delete': t('Удалить черновик', 'Qaralamanı sil', 'Delete draft'),
            'confirm': t('Удалить эту рабочую копию? Опубликованная карточка останется без изменений.', 'Bu iş nüsxəsi silinsin? Dərc edilmiş kart dəyişməyəcək.', 'Delete this working copy? The published card will stay unchanged.'),
            'cancel': t('Оставить', 'Saxla', 'Keep draft'),
            'error': t('Не удалось удалить. Обновите страницу и попробуйте ещё раз.', 'Silmək alınmadı. Səhifəni yeniləyin və yenidən cəhd edin.', 'Unable to delete. Refresh this page and try again.'),
            'needs_review': t('Карточка изменилась. Проверьте рабочую копию перед продолжением.',
                'Kart dəyişib. Davam etməzdən əvvəl iş nüsxəsini yoxlayın.',
                'The card has changed. Review your working copy before continuing.'),
            'pages': t('Страницы черновиков', 'Qaralama səhifələri', 'Draft pages'),
        }}
