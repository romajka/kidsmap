"""Contact exemptions by exact taxonomy, separate from approved place nature."""

OPTIONAL_CONTACT_TAXONOMY = {
    'parks-playgrounds': ('parks-boulevards', 'playgrounds'),
    'PARK': ('public-parks',),
}
CONTACT_FIELDS = ('phone1', 'phone2', 'phone3', 'website', 'whatsapp_number')


def contact_optional(*, category_code='', subcategory_code='', subcategory_category_code='', nature=''):
    return nature == 'public_space' or (
        bool(category_code) and category_code == subcategory_category_code
        and subcategory_code in OPTIONAL_CONTACT_TAXONOMY.get(category_code, ())
    )


def optional_taxonomy_q():
    from django.db.models import Q
    result = Q(pk__in=[])
    for category, codes in OPTIONAL_CONTACT_TAXONOMY.items():
        result |= Q(category_id=category, subcategory__category_id=category, subcategory__code__in=codes)
    return result


def contact_optional_q():
    from django.db.models import Q
    return Q(nature='public_space') | optional_taxonomy_q()


def contact_optional_for_place(place):
    sub = place.subcategory if getattr(place, 'subcategory_id', None) else None
    return contact_optional(category_code=getattr(place, 'category_id', '') or '',
                            subcategory_code=getattr(sub, 'code', '') or '',
                            subcategory_category_code=getattr(sub, 'category_id', '') or '',
                            nature=getattr(place, 'nature', '') or '')


def contact_client_config(instance, *, original_taxonomy=None, approved_nature=None):
    """Concrete IDs from the same allowlist; the browser never guesses taxonomy."""
    from django.db.models import Q
    from catalog.models import Subcategory
    from .place_readiness import inherited_contact_by_mode
    query = Q(pk__in=[])
    for category, codes in OPTIONAL_CONTACT_TAXONOMY.items():
        query |= Q(category_id=category, code__in=codes)
    pairs = {}
    for category, pk in Subcategory.objects.filter(query).values_list('category_id', 'pk'):
        pairs.setdefault(category, []).append(str(pk))
    original = original_taxonomy or (str(getattr(instance, 'category_id', '') or ''),
                                     str(getattr(instance, 'subcategory_id', '') or ''))
    inherited = {mode: bool(value) for mode, value in inherited_contact_by_mode(instance).items()}
    return dict(fields=list(CONTACT_FIELDS), optional_pairs=pairs,
                optional=(getattr(instance, 'nature', '') if approved_nature is None else approved_nature) == 'public_space',
                original_category=original[0], original_subcategory=original[1],
                inherited=inherited.get(getattr(instance, 'whatsapp_mode', 'legacy'), False),
                inherited_by_mode=inherited)
