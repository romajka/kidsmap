"""Indexable languages of approved public content, independent of URL slugs."""
from catalog.models import Activity
from catalog.services.public_presentation import (
    activity_text_source, activity_texts, current_organization, language_code, translated, visible,
)


def available_languages(entity):
    # AZ is the canonical baseline, including pre-Task33 legacy Place text.
    languages = ['az']
    if isinstance(entity, Activity):
        if not visible(entity):
            return []
        source = activity_text_source(entity, current_organization(entity.place))
        base = activity_texts(entity, 'az', source)
        if not base['name'].strip() or not base['description'].strip():
            languages = []
    for code in ('ru', 'en'):
        if isinstance(entity, Activity):
            # Resolve Program inheritance/snapshots through the approved reader.
            data = activity_texts(entity, code, source)
            complete = (data['name'].strip() and data['description'].strip()
                        and data['name_language'] == code and data['description_language'] == code
                        and (not data['supplement'] or data['supplement_language'] == code))
        else:
            name, name_language = translated(entity, 'name', code)
            description, description_language = translated(entity, 'description', code)
            complete = (name.strip() and description.strip()
                        and name_language == code and description_language == code)
        if complete:
            languages.append(code)
    return languages


def canonical_language(entity, language=None):
    code = language_code(language)
    return code if code in available_languages(entity) else 'az'
