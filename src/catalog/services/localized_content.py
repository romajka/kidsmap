"""Display existing public text without manufacturing stored translations."""
from django.utils.translation import get_language, gettext


def localized_content(obj, field, language=None):
    if field not in {'description', 'bio', 'education', 'experience_info'}:
        raise ValueError('Unsupported public text field')
    requested = (language or get_language() or 'az').split('-')[0]
    if requested not in {'az', 'ru', 'en'}:
        requested = 'az'
    # Preserve the specialist's established RU-first fallback where it exists.
    fallback = ('az', 'ru', 'en') if field == 'description' else ('ru', 'az', 'en')
    for source in dict.fromkeys((requested, *fallback)):
        text = getattr(obj, field + '_' + source, '') or ''
        if text.strip():
            return {'text': text, 'language': source, 'is_fallback': source != requested,
                    'source_label': gettext('Показан исходный текст (%(language)s).') % {'language': source.upper()}}
    return {'text': '', 'language': requested, 'is_fallback': False, 'source_label': ''}
