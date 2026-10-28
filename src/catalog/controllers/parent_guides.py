"""Useful editorial guides, independent of the number of catalog listings."""

import json
from math import cos, hypot, radians
from datetime import date
from urllib.parse import urlencode, urlsplit

from django.http import Http404
from django.db.models import Q, Subquery
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.views.decorators.http import require_safe

from catalog.models import Category, Place, Subcategory
from catalog.parent_guide_content import GUIDE_PAGES
from catalog.services.content_quality import public_place_queryset
from catalog.services.filtering import PlaceListFilters
from catalog.services.locations import get_location_translation
from catalog.services.public_presentation import prepare_cards
from catalog.services.public_urls import build_public_absolute_uri
from catalog.services.place_duplicates import normalize_place_name


def _json_ld(value):
    # Editorial text is data even when it includes an HTML-looking string.
    return json.dumps(value, ensure_ascii=False).translate(
        str.maketrans({'<': r'\u003c', '>': r'\u003e', '&': r'\u0026'})
    )


def _guide_venue_ids(candidates):
    """Collapse strong duplicate matches for this guide, retaining real branches.

    Names alone (or a chain's shared website) do not identify a venue. Require
    the same name/site/category and a location within 150 m; without coordinates
    require an identical nonempty address. Nothing is merged in the catalog.
    """
    ids = {}
    groups = {}
    for place in candidates:
        name = normalize_place_name(place)
        site = urlsplit(place._card_presentation['contacts']['website_url'])
        key = (name, site.netloc.casefold().removeprefix('www.'), site.path.rstrip('/'), place.category_id)
        peers = groups.setdefault(key, []) if name and site.netloc else []
        duplicate = None
        for peer in peers:
            if all(value is not None for value in (place.lat, place.lng, peer.lat, peer.lng)):
                north = (float(place.lat) - float(peer.lat)) * 111_320
                east = (float(place.lng) - float(peer.lng)) * 111_320 * cos(radians(float(place.lat)))
                same_location = hypot(north, east) <= 150
            else:
                address = ' '.join((place.address or '').casefold().split())
                same_location = bool(address) and address == ' '.join((peer.address or '').casefold().split())
            if same_location:
                duplicate = peer
                break
        ids[place.pk] = duplicate.pk if duplicate is not None else place.pk
        if duplicate is None:
            peers.append(place)
    return ids


DEFAULT_PARENT_GUIDE_SLUG = 'baku-with-kids'


@require_safe
def parent_guide_index(request):
    """Gracefully redirect root /parents/ to the flagship Baku guide."""
    slug = DEFAULT_PARENT_GUIDE_SLUG if DEFAULT_PARENT_GUIDE_SLUG in GUIDE_PAGES else next(iter(GUIDE_PAGES), None)
    if not slug:
        raise Http404
    target = reverse('parent_guide', kwargs={'slug': slug})
    query = request.META.get('QUERY_STRING')
    if query:
        target = f"{target}?{query}"
    return redirect(target, permanent=False)


@require_safe
def parent_guide(request, slug):
    language = (get_language() or 'az').split('-', 1)[0]
    definition = GUIDE_PAGES.get(slug)
    if definition is None or language not in definition['translations']:
        raise Http404
    guide = {
        **definition['translations'][language],
        'hero_image': definition['hero_image'],
        'updated': date.fromisoformat(definition['updated']),
    }
    public_places = public_place_queryset(Place.objects.all())
    topics = []
    active_categories = set(Category.active.values_list('pk', flat=True))
    subcategories = {row.code: row for row in Subcategory.active.all()}
    for topic in guide['topics']:
        params = {'category': topic['category'], 'district': 'baku'}
        available = topic['category'] in active_categories
        subcategory = subcategories.get(topic.get('subcategory'))
        if subcategory and subcategory.category_id == topic['category']:
            params['subcategory'] = subcategory.pk
        elif topic.get('subcategory'):
            available = False
        matching = PlaceListFilters(category=topic['category'], district='baku',
            subcategory=str(params.get('subcategory', ''))).apply(public_places) if available else public_places.none()
        topics.append({**topic, 'place_ids': list(matching.order_by('-updated_at', '-pk').values_list('pk', flat=True)[:6]),
            'count': matching.count(), 'url':
            reverse('place_list') + '?' + urlencode(params) if available else None})

    matching_categories = Q(pk__in=[])
    for category in definition['categories']:
        if category in active_categories:
            ids = PlaceListFilters(category=category, district='baku').apply(public_places).order_by().values('pk')
            matching_categories |= Q(pk__in=Subquery(ids))
    candidates = prepare_cards(public_places.filter(matching_categories).order_by('-updated_at', '-pk'), language)
    candidates = [place for place in candidates if place._card_presentation['visible']]
    venue_ids = _guide_venue_ids(candidates)
    by_id = {place.pk: place for place in candidates if venue_ids[place.pk] == place.pk}
    for topic in topics:
        topic['place_ids'] = list(dict.fromkeys(venue_ids[pk] for pk in topic['place_ids'] if pk in venue_ids))

    # Give each direction a turn; duplicate database rows must not displace
    # another venue, and new museums must not displace all other directions.
    selected_ids = []
    for rank in range(6):
        for topic in topics:
            if rank < len(topic['place_ids']):
                pk = topic['place_ids'][rank]
                if pk not in selected_ids and len(selected_ids) < 6:
                    selected_ids.append(pk)

    places = []
    if len(selected_ids) < 6:
        selected_ids.extend(pk for pk in by_id if pk not in selected_ids)
        selected_ids = selected_ids[:6]
    # Answers use the same public visibility and taxonomy as the venue cards.
    # A missing price is never evidence of free admission.
    faq_selections = []
    for item in guide['faq']:
        if item.get('free_only'):
            ids = [place.pk for place in by_id.values()
                if place._card_presentation['prices']['kind'] == 'free'][:3]
        else:
            sources = [topic['place_ids'] for topic in topics if topic['key'] in item.get('topic_keys', ())]
            ids = []
            for rank in range(6):
                for source in sources:
                    if rank < len(source) and source[rank] not in ids and len(ids) < 3:
                        ids.append(source[rank])
        faq_selections.append((item, ids))
    for pk in selected_ids:
        place = by_id.get(pk)
        if place is None:
            continue
        card = place._card_presentation
        if card['visible']:
            places.append({'id': place.pk, 'name': card['name'], 'url': card['url'],
                           'image_url': card['image_url'],
                           'name_language': card['name_language'],
                           'description': Truncator(strip_tags(card['description'])).chars(145),
                           'description_language': card['description_language'],
                           'topics': [topic['title'] for topic in topics if pk in topic['place_ids']] or [card['category_label']],
                           'location': get_location_translation(place.district, language),
                           'address': place.address_i18n(language)})
    faq_items = []
    for item, ids in faq_selections:
        related = []
        for pk in ids:
            place = by_id.get(pk)
            if place is not None and place._card_presentation['visible']:
                card = place._card_presentation
                related.append({'id': pk, 'name': card['name'], 'url': card['url'],
                    'name_language': card['name_language']})
        faq_items.append({**item, 'places': related})
    topic_by_key = {topic['key']: topic for topic in topics}
    faq_keys = {item.get('key') for item in faq_items}
    quick_choices = []
    for item in guide.get('quick_choices', ()):
        topic = topic_by_key.get(item.get('topic'))
        url = topic['url'] if topic else (
            '#guide-faq-' + item['faq'] if item.get('faq') in faq_keys else None)
        if url:
            quick_choices.append({'key': item.get('topic') or item['faq'], 'label': item['label'], 'url': url})
    catalog_url = reverse('place_list') + '?district=baku'
    if slug == 'baku-with-kids':
        catalog_url = (reverse('place_list') + '?' + urlencode({'category': 'FUN', 'district': 'baku'})
            if 'FUN' in active_categories else next((topic['url'] for topic in topics if topic['url']), '#guide-topics'))
    canonical = build_public_absolute_uri(request, reverse('parent_guide', kwargs={'slug': slug}))
    home_url = build_public_absolute_uri(request, reverse('home'))
    related_slug = 'baku-with-kids' if slug == 'sport' else 'sport'
    article = {
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': guide['title'], 'description': guide['meta_description'],
        'inLanguage': language, 'mainEntityOfPage': canonical,
        'dateModified': definition['updated'],
        'author': {'@type': 'Organization', 'name': 'KidsMap', 'url': home_url},
        'publisher': {'@type': 'Organization', 'name': 'KidsMap', 'url': home_url},
        'image': build_public_absolute_uri(request, static(guide['hero_image'])),
    }
    if definition.get('published'):
        article['datePublished'] = date.fromisoformat(definition['published']).isoformat()
    breadcrumbs = {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'KidsMap', 'item': home_url},
            {'@type': 'ListItem', 'position': 2, 'name': guide['title'], 'item': canonical},
        ],
    }
    return render(request, 'pages/parent_guide.html', {
        'guide': guide, 'guide_slug': slug, 'guide_topics': topics, 'guide_places': places,
        'guide_related_url': reverse('parent_guide', kwargs={'slug': related_slug}),
        'guide_catalog_url': catalog_url, 'guide_add_url': reverse('add_place'),
        'guide_quick_choices': quick_choices, 'guide_faq': faq_items,
        'seo_title': guide.get('seo_title', guide['title']) + ' — KidsMap',
        'guide_article_json': _json_ld(article), 'guide_breadcrumbs_json': _json_ld(breadcrumbs),
    })
