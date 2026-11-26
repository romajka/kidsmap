"""Page context for the afisha hub and its collections (SEO, answer card, FAQ, links).

The event list itself always comes from PlaceController.build_events_landing_context,
so a collection page looks and behaves exactly like the afisha with filters set.
"""
from urllib.parse import urlencode

from django.http import QueryDict
from django.utils.translation import override

from catalog.services import event_collections as ec
from catalog.services.afisha_urls import localized_route_paths
from catalog.services.public_urls import build_public_absolute_uri
from catalog.services.seo import _build_breadcrumb_schema, _build_item_list_schema, _serialize_json_ld

HUB_LABEL = {'az': 'Afişa', 'ru': 'Афиша', 'en': 'Events'}
HOME_LABEL = {'az': 'Ana səhifə', 'ru': 'Главная', 'en': 'Home'}
HUB_TITLE = {
    'az': 'Bakıda uşaqlar üçün tədbirlər',
    'ru': 'Детская афиша Баку',
    'en': 'Kids’ events in Baku',
}


def build_with_params(request, builder, params: dict):
    """Run the afisha context builder as if the request carried `params`."""
    original = request.GET
    fake = QueryDict(mutable=True)
    for key, value in params.items():
        fake[key] = value
    page = original.get('page')
    if page:
        fake['page'] = page
    request.GET = fake
    try:
        return builder(request)
    finally:
        request.GET = original


def _item_list(request, context, name):
    items = []
    for position, group in enumerate(context.get('event_groups') or [], start=1):
        event = group['event']
        items.append({'position': position, 'name': str(event.name_i18n()),
                      'url': build_public_absolute_uri(request, event.get_absolute_url())})
    if not items:
        return ''
    return _build_item_list_schema(name=name, item_urls=items, total_count=context['page_obj'].paginator.count)


def _faq_schema(items):
    return _serialize_json_ld({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {'@type': 'Question', 'name': item['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': item['a']}}
            for item in items
        ],
    })


def _breadcrumbs(request, items):
    schema = _build_breadcrumb_schema([
        {'name': item['name'], 'url': build_public_absolute_uri(request, item['url'])} for item in items
    ])
    return items, schema


def _home_path(language):
    from django.urls import reverse
    with override(language):
        return reverse('home')


def _chip_urls(request, context, language, categories):
    """Date and «free» chips lead to collection pages whenever one matches."""
    urls = dict(context.get('events_quick_urls') or {})
    current = {key: value for key, value in request.GET.items()
               if key not in {'page', 'date_filter', 'date', 'month', 'date_from', 'date_to', 'when', 'view'}}
    for key in ec.QUICK_TIMES:
        collection = ec.collection_for_query(dict(current, date_filter=key), categories=categories)
        if collection is not None:
            urls[key] = collection.path(language, categories)
    if not current:
        urls['all'] = ec.landing_path(language)
    return urls


def apply_hub(request, context, *, language, now):
    """Main afisha page: localized hreflang, collection links, answer card and FAQ."""
    categories = ec.category_rows()
    request._seo_localized_paths = localized_route_paths('events_landing')
    if context.get('events_mode') == 'list':
        context['events_quick_urls'] = _chip_urls(request, context, language, categories)
    if request.GET:
        return context
    title = HUB_TITLE[language]
    facts = ec.collection_facts(ec.query_public_events({}, now=now), now=now, language=language)
    faq = ec.faq_items(None, title, facts, language)
    context.update({
        'afisha_hub': True,
        'afisha_answer': ec.answer_text(title, facts, language),
        'afisha_updated': facts['updated'],
        'afisha_faq': faq,
        'afisha_links': ec.hub_links(language, now=now, categories=categories),
        'afisha_links_title': {'az': 'Hazır seçimlər', 'ru': 'Готовые подборки', 'en': 'Quick picks'}[language],
    })
    schemas = [_faq_schema(faq)]
    item_list = _item_list(request, context, title)
    if item_list:
        schemas.insert(0, item_list)
    context['afisha_schemas'] = schemas
    return context


def apply_collection(request, context, collection, *, language, now, categories):
    """Collection page: own H1/title/description, answer card, FAQ, neighbours."""
    title = ec.heading(collection, language, categories)
    label = ec.short_label(collection, language, categories)
    queryset = ec.collection_queryset(collection, now=now)
    facts = ec.collection_facts(queryset, now=now, language=language)
    indexable = ec.is_indexable(collection, now=now)
    canonical = collection.path(language, categories)

    request._seo_localized_paths = collection.paths(categories)
    request._seo_events_page_number = context['page_obj'].number
    if not indexable:
        request._seo_robots = 'noindex,follow'

    quick, counts = ec.quick_urls(collection, language, now=now, categories=categories)
    quick['past'] = ''
    stats = dict(context.get('events_quick_stats') or {})
    stats.update({key: counts[key] for key in ec.QUICK_TIMES})
    stats['total'] = counts['total'] if counts['total'] is not None else stats.get('total')
    stats['past'] = 0

    calendar_params = {key: value for key, value in collection.params().items()
                       if key not in ('date_filter', 'upcoming_month')}
    if collection.is_month:
        calendar_params['month'] = collection.time
    calendar_params['view'] = 'calendar'

    fallback = []
    if facts['total'] < ec.MIN_INDEXABLE_EVENTS:
        from catalog.services.event_afisha import upcoming_events_for_home
        shown = {group['event'].pk for group in context.get('event_groups') or []}
        fallback = [{'event': event, 'sessions': [], 'multi': False}
                    for event in upcoming_events_for_home(limit=9, now=now) if event.pk not in shown][:6]

    hub = ec.landing_path(language)
    crumbs, crumb_schema = _breadcrumbs(request, [
        {'name': HOME_LABEL[language], 'url': _home_path(language)},
        {'name': HUB_LABEL[language], 'url': hub},
        {'name': label, 'url': canonical},
    ])
    faq = ec.faq_items(collection, title, facts, language)
    schemas = [crumb_schema]
    item_list = _item_list(request, context, title)
    if item_list:
        schemas.append(item_list)
    schemas.append(_faq_schema(faq))

    free_label = {'az': 'pulsuz', 'ru': 'бесплатно', 'en': 'free'}[language]
    hero_stats = [{'value': facts['total'], 'label': {'az': 'seçimdə', 'ru': 'в подборке', 'en': 'in this list'}[language],
                   'kind': 'total'}]
    if facts['running']:
        hero_stats.insert(0, {'value': facts['running'], 'label': {'az': 'indi gedir', 'ru': 'идут сейчас', 'en': 'on now'}[language],
                              'kind': 'live'})
    if facts['free'] and not collection.free:
        hero_stats.append({'value': facts['free'], 'label': free_label, 'kind': ''})
    if facts['age_low'] is not None and facts['age_high'] is not None and len(hero_stats) < 3:
        hero_stats.append({'value': f"{facts['age_low']}–{facts['age_high']}",
                           'label': {'az': 'yaş', 'ru': 'лет', 'en': 'years old'}[language], 'kind': ''})

    context.update({
        'collection': collection,
        'collection_label': label,
        'collection_indexable': indexable,
        'collection_crumbs': crumbs,
        'collection_stats': hero_stats,
        'collection_fallback': fallback,
        'afisha_answer': ec.answer_text(title, facts, language),
        'afisha_updated': facts['updated'],
        'afisha_faq': faq,
        'afisha_links': ec.related_links(collection, language, now=now, categories=categories),
        'afisha_links_title': {'az': 'Bunlara da baxın', 'ru': 'Смотрите также', 'en': 'See also'}[language],
        'afisha_schemas': schemas,
        'events_breadcrumbs_json': '',
        'seo_title': ec.seo_title(collection, language, categories),
        'meta_description': ec.meta_description(title, language, facts['total']),
        'events_heading': title,
        'events_intro': ec.HERO_INTRO[language],
        'events_quick_urls': quick,
        'events_quick_stats': stats,
        'events_mode_urls': {'list': canonical, 'calendar': f'{hub}?{urlencode(calendar_params)}'},
        'query_without_page': '',
        # The collection itself is not a user filter: no «applied» badge.
        'has_active_filters': False,
    })
    return context
