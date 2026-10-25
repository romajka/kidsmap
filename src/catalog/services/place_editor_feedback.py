"""One-time editor outcomes, queued only after the database action commits."""
from django.db import transaction

_SESSION_KEY = '_km_place_editor_result'
_ACTIONS = frozenset({'draft', 'save', 'moderation', 'publish'})
_OWNER_DESTINATIONS = frozenset({'owner_place_create', 'owner_place_edit', 'owner_places_dashboard'})


def queue_editor_result(request, *, action, message):
    if action not in _ACTIONS:
        raise ValueError('Unsupported editor action')
    result = {'action': action, 'outcome': 'success', 'message': str(message)}
    transaction.on_commit(lambda: request.session.__setitem__(_SESSION_KEY, result))


def editor_result_context(request):
    user = getattr(request, 'user', None)
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_active', False):
        return {}
    if getattr(request, 'site_preview', False):
        return {}
    name = getattr(getattr(request, 'resolver_match', None), 'url_name', '')
    if name not in _OWNER_DESTINATIONS and not request.path.startswith('/admin/'):
        return {}
    if request.method != 'GET':
        # A failed native POST renders a bound form. Do not replay an older
        # successful action after it; read-only preview requests are excluded.
        request.session.pop(_SESSION_KEY, None)
        return {}
    result = request.session.pop(_SESSION_KEY, None)
    if not isinstance(result, dict) or result.get('action') not in _ACTIONS or result.get('outcome') != 'success':
        return {}
    return {'place_editor_result': result}
