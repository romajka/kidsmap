"""Actor-private place drafts shown before they become Place records."""
from urllib.parse import urlencode

from django.urls import reverse
from django.utils.translation import get_language

from catalog.models import ServerDraft


def new_place_working_drafts(*, user):
    return ServerDraft.objects.filter(
        actor=user, target_type='place', target_id__isnull=True,
        materialized_place__isnull=True,
    ).order_by('-saved_at', '-pk')


def draft_readiness_summary(draft, *, instance=None):
    from catalog.forms import OwnerPlaceEditForm
    from catalog.models import Place
    from catalog.services.place_editor_readiness import editor_readiness
    from catalog.services.server_drafts import json_value
    from django.http import QueryDict

    data = QueryDict('', mutable=True)
    if isinstance(getattr(draft, 'fields', None), dict):
        for key, value in draft.fields.items():
            data[key] = json_value(value)

    target_instance = instance or Place()
    form = OwnerPlaceEditForm(data=data, instance=target_instance, draft_save_only=True)
    form.is_valid()
    readiness = editor_readiness(form)

    req_count = readiness.get('required_count', 0)
    comp_count = readiness.get('completed_count', 0)
    percent = int(round((comp_count / req_count) * 100)) if req_count > 0 else 0
    percent = max(0, min(100, percent))

    tier = 'high' if percent >= 80 else ('medium' if percent >= 40 else 'low')

    missing_items = [
        issue.get('label') for issue in readiness.get('issues', [])
        if issue.get('label')
    ]
    completed_items = [
        item.get('label') for item in readiness.get('items', [])
        if item.get('complete') and item.get('label')
    ]

    readiness['percentage'] = percent
    readiness['tier'] = tier
    readiness['missing_labels'] = missing_items
    readiness['completed_labels'] = completed_items
    return readiness


def place_working_draft_card(draft, *, language=None, include_readiness=False, readiness=None):
    language = (language or get_language() or 'az').split('-')[0]
    title = next((draft.fields.get(key) for key in (
        'name_'+language, 'name_az', 'name_ru', 'name_en',
    ) if draft.fields.get(key)), None)
    fallback = {'az': 'Yeni məkan', 'ru': 'Новое место', 'en': 'New place'}
    url = reverse('owner_place_edit', args=[draft.target_id]) if draft.target_id else reverse('owner_place_create')
    card = {
        'id': str(draft.pk), 'version': draft.version,
        'title': title or fallback.get(language, fallback['az']),
        'saved_at': draft.saved_at,
        'delete_url': reverse('server_draft_detail', args=[draft.pk]),
        'url': url+'?'+urlencode({'type': 'permanent', 'draft_id': str(draft.pk), 'draft_session': str(draft.pk)}),
    }
    if readiness is not None:
        card['readiness'] = readiness
    elif include_readiness:
        card['readiness'] = draft_readiness_summary(draft)
    return card


def working_drafts_overview(*, user):
    drafts = new_place_working_drafts(user=user)
    return {
        'working_drafts_overview_count': drafts.count(),
        'working_drafts_overview': [place_working_draft_card(draft, include_readiness=True) for draft in drafts[:4]],
    }
