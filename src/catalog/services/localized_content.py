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


def separate_bilingual_note(value, language=None):
    """Select only clearly separate RU/AZ paragraphs in old bilingual notes.

    Never guess English translations, split a sentence, or alter a monolingual
    note. Neutral lines (prices, names, links) remain with their preceding block.
    Stored text is not changed.
    """
    import re
    requested = (language or '').split('-')[0]
    if requested not in {'ru', 'az'}:
        return value
    blocks, current = [], None
    for line in str(value or '').splitlines():
        ru = len(re.findall(r'[А-Яа-яЁё]', line))
        az = len(re.findall(r'[ƏəĞğİıÖöŞşÜüÇç]', line))
        latin = len(re.findall(r'[A-Za-zƏəĞğİıÖöŞşÜüÇç]', line))
        source = 'ru' if ru >= 12 and ru > latin else ('az' if ru == 0 and az >= 2 and latin >= 12 else None)
        if source and source != current:
            blocks.append([source, []])
            current = source
        if not blocks:
            blocks.append([None, []])
        blocks[-1][1].append(line)
    if {source for source, _ in blocks} >= {'ru', 'az'}:
        return '\n'.join(line for source, lines in blocks if source in {None, requested} for line in lines).strip()
    return value
