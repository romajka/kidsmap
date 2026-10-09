"""Published presentation shared by SSR details, cards, maps and SEO.

Never reads revision payloads. Local approved snapshots may survive a detach;
live Program/Organization inheritance requires a current published affiliation.
"""
import copy
import re
from urllib.parse import urlsplit
from django.urls import reverse
from django.utils.translation import get_language, override
from catalog.models import Place, Organization, Program, Activity
from catalog.services.organization_ownership import affiliation_current
from catalog.services.pricing_plans import build_public_price_summary, format_price_amount, plan_billing_unit


def language_code(language=None):
    value = (language or get_language() or 'az').split('-')[0]
    return value if value in {'az', 'ru', 'en'} else 'az'


def translated(obj, field, language):
    getter = obj.get if isinstance(obj, dict) else lambda name, default='': getattr(obj, name, default)
    text = getter(f'{field}_{language}', '') or ''
    if text.strip():
        return text, language
    text = getter(f'{field}_az', '') or ''
    if text.strip():
        return text, 'az'
    # Pre-task33 Place records may have only the legacy text columns.
    if isinstance(obj, Place):
        return getter(field, '') or '', 'az'
    return '', language


def visible(obj):
    if getattr(obj, "_public_batch", False):
        return obj._public_visible
    if isinstance(obj, Place):
        return Place.objects.filter(pk=obj.pk, status='published', is_active=True, deleted_at__isnull=True).exists()
    if isinstance(obj, (Organization, Program)):
        return type(obj).objects.filter(pk=obj.pk, status='published', archived_at__isnull=True, approved_at__isnull=False).exists()
    if isinstance(obj, Activity):
        return Activity.objects.filter(pk=obj.pk, status='published', archived_at__isnull=True,
            place__status='published', place__is_active=True, place__deleted_at__isnull=True).exists()
    return False


def current_organization(place):
    if getattr(place, "_public_batch", False):
        return place._public_organization
    # Inherited contacts must not trust a related-object cache retained over detach/transfer.
    current = Place.objects.select_related('organization').filter(pk=place.pk).first()
    org = current.organization if current and current.organization_id else None
    return org if org and visible(org) and affiliation_current(current, org) else None


def safe_web_url(value):
    value = (value or '').strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ''
    return value if parsed.scheme in {'http', 'https'} and parsed.netloc and not parsed.username and not parsed.password else ''


def contact_data(obj):
    place = obj.place if isinstance(obj, Activity) else obj if isinstance(obj, Place) else None
    org = current_organization(place) if place else obj if isinstance(obj, Organization) and visible(obj) else None
    phones = list(place.phone_numbers) if place else []
    local_website = safe_web_url(place.website_url()) if place else ''
    phone_source = 'place' if phones else 'organization' if org and org.phone else ''
    if not phones and org and org.phone:
        phones = [org.phone]
    website = safe_web_url(local_website or (org.website if org else ''))
    website_source = 'place' if local_website else 'organization' if website else ''
    whatsapp_contact = phones[0] if phone_source == 'place' else (org.whatsapp if org else '') or (phones[0] if phones else '')
    whatsapp = re.sub(r'\D', '', whatsapp_contact)
    if whatsapp.startswith('0'):
        whatsapp = '994' + whatsapp[1:]
    return {'phones': phones, 'has_phone': bool(phones), 'website_url': website,
        'whatsapp_url': 'https://wa.me/' + whatsapp if whatsapp else '',
        'source': 'organization' if phone_source == 'organization' or website_source == 'organization' else 'place' if place else '',
        'sources': {'phone': phone_source, 'website': website_source}}


def public_url(obj, language=None):
    with override(language_code(language)):
        if isinstance(obj, Place):
            return obj.get_absolute_url()
        if isinstance(obj, Organization):
            return reverse('organization_detail', args=[obj.public_id])
        if isinstance(obj, Activity):
            return reverse('activity_detail', args=[obj.pk])
        return ''


def price_rows(group, language):
    rows = []
    words = {'az': ('Pulsuz', 'Qiymət dəqiqləşdirilir', '-dən'), 'ru': ('Бесплатно', 'Цена уточняется', 'от'), 'en': ('Free', 'Price on request', 'from')}[language]
    plans = group._public_plans if hasattr(group, '_public_plans') else group.pricing_plan_records.filter(is_active=True).order_by('sort_order', 'pk')
    for plan in plans:
        if plan.price_kind == 'free':
            label = words[0]
        elif plan.price_kind == 'on_request':
            label = words[1]
        elif plan.price_kind == 'range':
            label = f'{format_price_amount(plan.price_min)}–{format_price_amount(plan.price_max)} {plan.currency}'
        elif plan.price_kind == 'from':
            amount = format_price_amount(plan.price_min)
            label = f'{amount} {plan.currency}-dən' if language == 'az' else f'{words[2]} {amount} {plan.currency}'
        else:
            label = f'{format_price_amount(plan.price)} {plan.currency}'
        unit = plan_billing_unit(plan, language)
        if unit and plan.price_kind not in {'free', 'on_request'}:
            label += ' / ' + unit
        with override(language):
            title = plan.title_i18n(language)
            conditions = plan.conditions_i18n(language)
        rows.append({'id':plan.pk, 'title':title, 'label':label,
            'title_language': _price_text_language(plan, 'title', language),
            'conditions':conditions, 'conditions_language': _price_text_language(plan, 'conditions', language),
            'is_required':plan.is_required, 'is_trial':plan.is_trial})
    return rows


def _price_text_language(plan, field, language):
    # Match PricingPlan's existing fallback order, including legacy RU/EN text.
    return next((code for code in dict.fromkeys((language, 'az', 'ru', 'en'))
                 if getattr(plan, f'{field}_{code}', '')), language)


def activity_groups(activity, language):
    result = []
    groups = activity._public_groups if hasattr(activity, '_public_groups') else activity.offering_groups.filter(archived_at__isnull=True).prefetch_related('pricing_plan_records')
    for group in groups:
        low, high = group.age_from, group.age_to
        age = f'{low}–{high}' if low is not None and high is not None else f'{low}+' if low is not None else f'≤ {high}' if high is not None else ''
        name, name_lang = translated(group, 'name', language)
        conditions, conditions_lang = translated(group, 'conditions', language)
        result.append({'id':group.pk,'name':name, 'name_language':name_lang, 'age':age,
            'language':group.language, 'schedule':group.schedule_text, 'teachers':group.teachers_text,
            'conditions':conditions, 'conditions_language':conditions_lang, 'prices':price_rows(group,language)})
    return result


def schema_offers(place, lang):
    """Canonical tariff offers used by public SEO; preserve billing and required fees."""
    from catalog.services.pricing_plans import place_pricing_records
    pricing_records = list(place_pricing_records(place))
    offers = []
    for plan in pricing_records:
        if not plan.is_active or plan.charge_role != "primary" or plan.is_trial:
            continue
        if plan.price_kind not in {"exact", "free", "range", "from"}:
            continue
        with override(lang):
            offer_name = plan.title_i18n(lang)
        offer = {"@type": "Offer", "name": offer_name, "priceCurrency": plan.currency}
        descriptions = []
        period = plan_billing_unit(plan, lang)
        if period:
            descriptions.append({"ru": "Оплата за", "az": "Ödəniş", "en": "Billed per"}.get(lang, "Billed per") + f" {period}")
        if plan.offering_group_id:
            fees = [row for row in pricing_records if row.offering_group_id == plan.offering_group_id and row.is_active and row.is_required and row.charge_role != "primary"]
            for fee in fees:
                fee_amount = fee.price if fee.price_kind in {"exact", "free"} else fee.price_min
                if fee_amount is not None:
                    prefix = {"ru": "Обязательный платёж", "az": "Məcburi ödəniş", "en": "Required fee"}.get(lang, "Required fee")
                    with override(lang):
                        fee_name = fee.title_i18n(lang)
                    descriptions.append(f"{prefix}: {fee_name} {format_price_amount(fee_amount)} {fee.currency}")
        if descriptions:
            offer["description"] = "; ".join(descriptions)
        if plan.price_kind in {"exact", "free"}:
            offer["price"] = format(plan.price, ".2f")
        elif plan.price_kind == "from":
            val = plan.price_min if plan.price_min is not None else plan.price
            if val is not None:
                offer["price"] = format(val, ".2f")
                offer["priceSpecification"] = {
                    "@type": "PriceSpecification",
                    "minPrice": format(val, ".2f"),
                    "priceCurrency": plan.currency,
                }
        elif plan.price_min is not None and plan.price_max is not None:
            offer["priceSpecification"] = {
                "@type": "PriceSpecification",
                "minPrice": format(plan.price_min, ".2f"),
                "maxPrice": format(plan.price_max, ".2f"),
                "priceCurrency": plan.currency,
            }
        offers.append(offer)

    if not offers:
        price_mode = getattr(place, "price_mode", Place.PRICE_MODE_TARIFFS) or Place.PRICE_MODE_TARIFFS
        if price_mode == Place.PRICE_MODE_FREE:
            free_label = {"az": "Pulsuz", "ru": "Бесплатно", "en": "Free"}.get(lang, "Бесплатно")
            offers.append({
                "@type": "Offer",
                "name": free_label,
                "price": "0.00",
                "priceCurrency": "AZN",
            })

    return offers if len(offers) > 1 else offers[0] if offers else []


def activity_text_source(activity, organization):
    """Approved live source or permitted detached snapshot; never a candidate."""
    program = activity.program if activity.program_id else None
    return (program if program and visible(program) and organization
            and program.organization_id == organization.pk
            else activity.program_snapshot if not activity.program_id
            or (organization and program and program.organization_id == organization.pk) else {})


def activity_texts(activity, language, source):
    """Text/provenance only, sharing precisely the public inheritance contract."""
    name, name_lang = translated(activity, 'name', language)
    description, description_lang = translated(activity, 'description', language)
    if not name:
        name, name_lang = translated(source, 'name', language)
    if source:
        description, description_lang = translated(source, 'description', language)
    supplement, supplement_lang = translated(activity, 'supplement', language)
    return {'name': name, 'name_language': name_lang,
            'description': description, 'description_language': description_lang,
            'supplement': supplement, 'supplement_language': supplement_lang}


def present(obj, language=None):
    lang = language_code(language)
    kind = obj._meta.model_name
    result = {'kind':kind, 'id':obj.pk, 'visible':visible(obj), 'name':'', 'description':'',
        'supplement':'', 'url':'', 'translation_fallback':False, 'content_language':lang,
        'name_language':lang, 'description_language':lang, 'supplement_language':lang,
        'image_url':'', 'placeholder_icon':'location_on', 'category_label':'', 'contacts':{},
        'prices':{}, 'groups':[], 'organization':None}
    if not result['visible']:
        return result
    name, name_lang = translated(obj,'name',lang)
    description, description_lang = translated(obj,'description',lang)
    place = obj if isinstance(obj, Place) else obj.place if isinstance(obj, Activity) else None
    org = current_organization(place) if place else obj.organization if isinstance(obj, Program) and visible(obj.organization) else None
    if isinstance(obj, Activity):
        text = activity_texts(obj, lang, activity_text_source(obj, org))
        name, name_lang = text['name'], text['name_language']
        description, description_lang = text['description'], text['description_language']
        result.update(supplement=text['supplement'], supplement_language=text['supplement_language'])
        result['groups'] = activity_groups(obj,lang)
        result['translation_fallback'] = bool(result['supplement'] and text['supplement_language'] != lang)
    result.update(name=name, description=description, name_language=name_lang,
        description_language=description_lang, url=public_url(obj,lang),
        contacts=contact_data(obj), content_language='az' if (name and name_lang != lang) or (description and description_lang != lang) else lang)
    result['translation_fallback'] |= result['content_language'] != lang
    if isinstance(obj, Activity):
        from catalog.models import Category
        from catalog.services.catalog_structure import activity_taxonomy_ids
        category_id, subcategory_id = activity_taxonomy_ids(obj)
        category = (obj._public_taxonomy_category if hasattr(obj, '_public_taxonomy_category')
                    else Category.objects.filter(pk=category_id).first() if category_id else None)
        result.update(category_id=category_id, subcategory_id=subcategory_id)
    else:
        category = place.category if place else getattr(obj,'category',None)
    if category:
        result['category_label'] = category.name_i18n(lang)
        result['placeholder_icon'] = category.code
    if place:
        from catalog.services.map_payload import map_identity
        result['map_available'] = map_identity(place) is not None
        result['image_url'] = place.public_image_url
        from catalog.services.features import is_organizations_section_enabled
        if org and is_organizations_section_enabled():
            org_name, org_lang = translated(org, 'name', lang)
            result['organization'] = {'name':org_name, 'name_language':org_lang, 'url':public_url(org,lang)}
        price_place = place
        if isinstance(obj, Activity):
            price_place = copy.copy(place)
            groups = obj._public_groups if hasattr(obj, '_public_groups') else obj.offering_groups.filter(archived_at__isnull=True)
            price_place._pricing_records_cache = [p for g in groups for p in (g._public_plans if hasattr(g, '_public_plans') else g.pricing_plan_records.filter(is_active=True))]
            price_place.price_mode = 'tariffs'
            price_place.price_from = price_place.price_to = None
            for code in ('az','ru','en'):
                setattr(price_place, 'custom_price_badge_' + code, '')
        result['prices'] = build_public_price_summary(price_place,lang)
        result['prices']['schema_offers'] = schema_offers(price_place,lang)
    return result


def prepare_cards(places, language=None, *, filters=None):
    """Fresh batch presentation for a single request, with a constant query budget.

    Batch trust markers exist only while materializing this snapshot. Direct
    detail/contact resolver calls still recheck visibility and affiliation.
    """
    from django.db.models import Exists, OuterRef, Prefetch, QuerySet
    from catalog.models import OfferingGroup, PricingPlan
    from catalog.services.catalog_search import matching_groups, has_offer_filters
    from catalog.services.pricing_plans import prefetch_place_pricing_records
    # Re-evaluate QuerySets directly: materializing their old prefetches and then
    # fetching the same rows again doubles schedule work. Lists still need a
    # fresh lookup because they may contain objects retained over an ACL change.
    queryset_input = isinstance(places, QuerySet)
    source = None if queryset_input else list(places)
    if source == []:
        return []
    lookup = places.all().prefetch_related(None) if queryset_input else Place.objects.filter(pk__in=[p.pk for p in source])
    live_activities = Activity.objects.filter(place_id=OuterRef('pk'), status='published', archived_at__isnull=True)
    fresh = {p.pk:p for p in lookup
        .select_related('organization', 'category', 'subcategory', 'confirmed_location')
        .annotate(_has_public_activities=Exists(live_activities))
        .prefetch_related('schedule_days__intervals')}
    if source is None:
        source = list(fresh.values())
    if not source:
        return []
    batch = [fresh[p.pk] for p in source if p.pk in fresh]
    plans = PricingPlan.objects.filter(is_active=True).order_by('sort_order','pk')
    groups = OfferingGroup.objects.filter(archived_at__isnull=True)
    if filters is not None:
        groups = matching_groups(filters)
    groups = groups.prefetch_related(Prefetch('pricing_plan_records',queryset=plans,to_attr='_public_plans'))
    activity_place_ids = [pk for pk, place in fresh.items() if place._has_public_activities]
    acts = Activity.objects.filter(place_id__in=activity_place_ids,status='published',archived_at__isnull=True)
    acts = acts.select_related('program__organization').prefetch_related(Prefetch('offering_groups',queryset=groups,to_attr='_public_groups'))
    by_place = {pk:[] for pk in fresh}
    activities = list(acts)
    from catalog.models import Category
    from catalog.services.catalog_structure import activity_taxonomy_ids
    category_ids = {activity_taxonomy_ids(activity)[0] for activity in activities}
    categories = Category.objects.in_bulk(category_ids - {None}) if category_ids - {None} else {}
    for activity in activities:
        activity._public_taxonomy_category = categories.get(activity_taxonomy_ids(activity)[0])
        activity.place = fresh[activity.place_id]
        by_place[activity.place_id].append(activity)
    prefetch_place_pricing_records(batch)
    exact = filters is not None and has_offer_filters(filters)
    offer_filtered = filters is not None and (exact or bool(filters.query))
    marked=[]
    def mark(row, is_visible=True):
        row._public_batch=True;row._public_visible=is_visible;marked.append(row)
    try:
        for place in batch:
            mark(place, place.status=='published' and place.is_active and place.deleted_at is None)
            org=place.organization if place.organization_id else None
            if org:
                mark(org,org.status=='published' and org.archived_at is None and org.approved_at is not None)
            place._public_organization = org if org and org._public_visible and affiliation_current(place,org) else None
        result=[]
        for old in source:
            place=fresh.get(old.pk)
            if place is None or not place._public_visible:
                continue
            place.is_liked=getattr(old,'is_liked',False)
            offers=[];matched_plans=[]
            for activity in by_place[place.pk]:
                mark(activity)
                if activity.program_id:
                    program=activity.program
                    mark(program,program.status=='published' and program.archived_at is None and program.approved_at is not None)
                    mark(program.organization, program.organization.status=='published' and program.organization.approved_at is not None and program.organization.archived_at is None)
                if filters is not None and not activity._public_groups:
                    continue
                data=present(activity,language)
                offers.append({'id':activity.pk,'name':data['name'],'url':data['url'],'groups':data['groups']})
                matched_plans.extend(p for g in activity._public_groups for p in g._public_plans)
            if offer_filtered and by_place[place.pk]:
                place._pricing_records_cache = matched_plans if offers else [p for p in place._pricing_records_cache if p.place_id == place.pk and p.offering_group_id is None]
                if offers:
                    place.price_mode='tariffs'
                place.price_from=place.price_to=None
                for code in ('az','ru','en'):
                    setattr(place,'custom_price_badge_'+code,'')
            presentation=present(place,language)
            presentation.update(matched_offers=offers,exact_filtered=exact)
            place._card_presentation=presentation
            result.append(place)
        return result
    finally:
        for row in marked:
            for attr in ('_public_batch','_public_visible','_public_organization'):
                if hasattr(row,attr):delattr(row,attr)


def organization_matches(query, language=None):
    """Name discovery links, including useful published Organizations without branches."""
    from django.db.models import Q
    from catalog.services.features import is_organizations_section_enabled
    if not query or not is_organizations_section_enabled():
        return []
    names=Q()
    for code in ('az','ru','en'):
        names |= Q(**{'name_'+code+'__icontains':query})
    rows=Organization.objects.filter(names,status='published',approved_at__isnull=False,archived_at__isnull=True).order_by('pk')[:12]
    lang=language_code(language)
    return [{'name':translated(row,'name',lang)[0],'url':public_url(row,lang)} for row in rows]
