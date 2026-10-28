"""Exact matching: one published activity and one real, unarchived group.

Taxonomy must be an approved activity snapshot; a branch's category cannot be
assigned to all of its lessons. Unknown legacy suitability remains discoverable
in the general catalog and by its direct URL.
"""
from django.db.models import Exists, F, OuterRef, Q
from catalog.models import Activity, OfferingGroup, PricingPlan


def current_org_q(prefix=''):
    return Q(**{prefix+'organization__status':'published',
        prefix+'organization__approved_at__isnull':False,
        prefix+'organization__archived_at__isnull':True,
        prefix+'organization_relationship_kind__in':('business','informational'),
        prefix+'organization_join_place_ownership_version':F(prefix+'ownership_version'),
        prefix+'organization_join_org_ownership_version':F(prefix+'organization__ownership_version')})


def text_q(query, prefix=''):
    result=Q()
    for field in ('name','name_az','name_ru','name_en','description_az','description_ru','description_en','address'):
        result |= Q(**{prefix+field+'__icontains':query})
    org=Q()
    for lang in ('az','ru','en'):
        org |= Q(**{prefix+'organization__name_'+lang+'__icontains':query})
    return result | (current_org_q(prefix) & org)


def has_offer_filters(filters):
    low, high=filters._normalized_age_bounds()
    return bool(filters.category or filters.subcategory or low is not None or high is not None)


def matching_groups(filters):
    qs=OfferingGroup.objects.filter(archived_at__isnull=True,activity__status='published',activity__archived_at__isnull=True)
    if filters.category:
        qs=qs.filter(offer_taxonomy_q('category_id',filters.category))
    if filters.subcategory:
        qs=qs.filter(offer_taxonomy_q('subcategory_id',int(filters.subcategory)))
    low,high=filters._normalized_age_bounds()
    if low is not None or high is not None:
        qs=qs.exclude(age_from__isnull=True,age_to__isnull=True)
    if low is not None:qs=qs.filter(Q(age_to__isnull=True)|Q(age_to__gte=low))
    if high is not None:qs=qs.filter(Q(age_from__isnull=True)|Q(age_from__lte=high))
    if filters.query:
        names=Q()
        for lang in ('az','ru','en'):
            names |= Q(**{'activity__name_'+lang+'__icontains':filters.query}) | Q(**{'name_'+lang+'__icontains':filters.query})
            names |= Q(**{'activity__program_snapshot__name_'+lang+'__icontains':filters.query})
        qs=qs.filter(text_q(filters.query,'activity__place__') | names)
    return qs


def offer_taxonomy_q(field,value):
    """Linked approved snapshot; standalone own taxonomy; old frozen copies only."""
    snapshot=Q(**{'activity__program_snapshot__'+field:value})
    if field=='subcategory_id':
        snapshot |= Q(activity__program_snapshot__subcategory_id=str(value))
    own=Q(activity__program__isnull=True,**{'activity__'+field:value})
    frozen=Q(activity__program__isnull=True,activity__category__isnull=True,
        activity__subcategory__isnull=True) & snapshot
    return own | (Q(activity__program__isnull=False) & snapshot) | frozen


def general_admission_q():
    return Q(nature='public_space',nature_approved_at__isnull=False) | Exists(
        PricingPlan.objects.filter(place_id=OuterRef('pk'),offering_group__isnull=True,is_active=True,product_type='admission'))


def taxonomy_counts(public_qs):
    """Distinct Place counts from the same mixed-reader taxonomy as search."""
    from collections import defaultdict
    categories=defaultdict(set);subcategories=defaultdict(set)
    live=Activity.objects.filter(place_id=OuterRef('pk'),status='published',archived_at__isnull=True)
    direct=public_qs.filter(~Exists(live)|general_admission_q())
    for pk, category, subcategory in direct.values_list('pk','category_id','subcategory_id'):
        if category:categories[category].add(pk)
        if subcategory:subcategories[str(subcategory)].add(pk)
    for pk,program_id,category_id,subcategory_id,snapshot in Activity.objects.filter(place_id__in=public_qs.values('pk'),status='published',archived_at__isnull=True,
        offering_groups__archived_at__isnull=True,offering_groups__isnull=False).values_list('place_id','program_id','category_id','subcategory_id','program_snapshot').distinct():
        from catalog.services.catalog_structure import taxonomy_ids
        category,subcategory=taxonomy_ids(program_id,category_id,subcategory_id,snapshot)
        if isinstance(category,str) and category:categories[category].add(pk)
        if isinstance(subcategory,(str,int)) and str(subcategory).isdigit():subcategories[str(subcategory)].add(pk)
    return ({key:len(value) for key,value in categories.items()}, {key:len(value) for key,value in subcategories.items()})


def place_audience_q(filters):
    """A confirmed admission age or an explicitly approximate place audience."""
    low, high = filters._normalized_age_bounds()
    audience = general_admission_q() | Q(age_varies_by_program=True)
    if filters.category: audience &= Q(category_id=filters.category)
    if filters.subcategory: audience &= Q(subcategory_id=filters.subcategory)
    if low is not None or high is not None:
        audience &= ~Q(age_from__isnull=True, age_to__isnull=True)
    if low is not None: audience &= Q(age_to__isnull=True) | Q(age_to__gte=low)
    if high is not None: audience &= Q(age_from__isnull=True) | Q(age_from__lte=high)
    if filters.query: audience &= text_q(filters.query)
    return audience


def apply_offer_matching(qs,filters):
    groups=matching_groups(filters).filter(activity__place_id=OuterRef('pk'))
    if has_offer_filters(filters):
        low,high=filters._normalized_age_bounds()
        admission = place_audience_q(filters)
        # Legacy taxonomy alone is useful browsing; category+age is never inferred.
        legacy=Q(pk__in=[])
        if low is None and high is None:
            legacy=~Exists(Activity.objects.filter(place_id=OuterRef('pk'),status='published',archived_at__isnull=True))
            if filters.category:legacy &= Q(category_id=filters.category)
            if filters.subcategory:legacy &= Q(subcategory_id=filters.subcategory)
            if filters.query:legacy &= text_q(filters.query)
        qs=qs.filter(Exists(groups)|admission|legacy)
    elif filters.query:
        qs=qs.filter(text_q(filters.query)|Exists(groups))
    return qs
