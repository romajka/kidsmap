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


def public_activities_with_languages():
    """Fresh sitemap snapshot; batch only the canonical reader's DB predicates.

    No trusted markers survive this call. The next generation always re-reads
    publication, affiliation versions and translations from the database.
    """
    from catalog.models import Place
    from catalog.services.content_quality import public_place_queryset
    from catalog.services.organization_ownership import affiliation_current

    rows = list(Activity.objects.filter(status='published', archived_at__isnull=True,
        place__in=public_place_queryset(Place.objects.all())).select_related(
        'place__category', 'place__organization', 'program__organization').order_by('pk'))
    marked = []

    def mark(obj, is_visible):
        obj._public_batch = True
        obj._public_visible = is_visible
        marked.append(obj)

    def approved(obj):
        return obj.status == 'published' and obj.archived_at is None and obj.approved_at is not None

    try:
        languages = {}
        for activity in rows:
            place = activity.place
            mark(place, place.status == 'published' and place.is_active and place.deleted_at is None)
            mark(activity, activity.status == 'published' and activity.archived_at is None and place._public_visible)
            org = place.organization if place.organization_id else None
            if org:
                mark(org, approved(org))
            place._public_organization = org if org and org._public_visible and affiliation_current(place, org) else None
            if activity.program_id:
                mark(activity.program, approved(activity.program))
            languages[activity.pk] = available_languages(activity)
        return rows, languages
    finally:
        for obj in marked:
            for attribute in ('_public_batch', '_public_visible', '_public_organization'):
                if hasattr(obj, attribute):
                    delattr(obj, attribute)
