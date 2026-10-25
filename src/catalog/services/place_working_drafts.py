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


def place_working_draft_card(draft, *, language=None):
    language = (language or get_language() or 'az').split('-')[0]
    title = next((draft.fields.get(key) for key in (
        'name_'+language, 'name_az', 'name_ru', 'name_en',
    ) if draft.fields.get(key)), None)
    fallback = {'az': 'Yeni məkan', 'ru': 'Новое место', 'en': 'New place'}
    url = reverse('owner_place_edit', args=[draft.target_id]) if draft.target_id else reverse('owner_place_create')
    return {
        'id': str(draft.pk), 'version': draft.version,
        'title': title or fallback.get(language, fallback['az']),
        'saved_at': draft.saved_at,
        'delete_url': reverse('server_draft_detail', args=[draft.pk]),
        'url': url+'?'+urlencode({'type': 'permanent', 'draft_id': str(draft.pk), 'draft_session': str(draft.pk)}),
    }


def working_drafts_overview(*, user):
    drafts = new_place_working_drafts(user=user)
    return {
        'working_drafts_overview_count': drafts.count(),
        'working_drafts_overview': [place_working_draft_card(draft) for draft in drafts[:4]],
    }
