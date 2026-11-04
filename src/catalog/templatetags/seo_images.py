"""Image previews from the content already selected for this public page.

No extra catalog queries, random cross-category photos, or site-logo fallback.
"""

from django import template

from catalog.services.public_urls import build_public_absolute_uri
from catalog.services.seo import _serialize_json_ld

register = template.Library()

PUBLIC_IMAGE_ROUTES = frozenset({
    'seo_landing', 'home', 'place_list', 'place_new', 'place_detail', 'parent_guide',
    'organization_list', 'organization_detail', 'activity_detail',
    'specialist_list', 'specialist_detail', 'events_landing', 'event_detail',
})


def _page_image(context, route, language):
    guide = context.get('guide_image')
    if guide:
        return guide['url'], guide['caption']
    if 'seo_image_url' in context:
        presentation = context.get('presentation') or {}
        return context['seo_image_url'], presentation.get('name') or context.get('seo_title', '')
    if route == 'seo_landing':
        for card in context.get('seo_featured_places') or []:
            if card.get('image_url'):
                return card['image_url'], card.get('name', '')
    if route == 'home':
        slides = context.get('hero_gallery_slides') or []
        if slides:
            main = slides[0]['main']
            return main.get('image_url', ''), main.get('label', '')
        return '', ''
    if route == 'organization_list':
        for card in context.get('cards') or []:
            for photo in card.get('photos') or []:
                if photo.get('url'):
                    return photo['url'], photo.get('name', '')
    if route == 'specialist_list':
        for specialist in context.get('specialists') or []:
            if getattr(specialist, 'has_valid_photo', False) and specialist.photo:
                return specialist.photo.url, specialist.name
    if route in {'place_list', 'place_new'}:
        for place in context.get('places') or []:
            card = getattr(place, '_card_presentation', {})
            if card.get('visible') and card.get('image_url'):
                return card['image_url'], card.get('name', '')
    if route in {'events_landing', 'place_list', 'place_new'}:
        for event in context.get('events') or []:
            if event.photo:
                return event.photo.url, event.name_i18n(language)
    return '', ''


@register.simple_tag(takes_context=True)
def public_image_preview(context):
    request = context.get('request')
    route = getattr(getattr(request, 'resolver_match', None), 'url_name', '')
    if route not in PUBLIC_IMAGE_ROUTES:
        return {}
    language = (getattr(request, 'LANGUAGE_CODE', '') or 'az').split('-')[0]
    url, alt = _page_image(context, route, language)
    if not url:
        return {}
    url = build_public_absolute_uri(request, url)
    alt = str(alt or context.get('seo_title') or 'KidsMap')
    canonical = context.get('canonical_url') or build_public_absolute_uri(request, request.path)
    webpage = {
        '@context': 'https://schema.org', '@type': 'WebPage',
        '@id': canonical, 'url': canonical,
        'name': str(context.get('seo_title') or alt), 'inLanguage': language,
        'primaryImageOfPage': {'@type': 'ImageObject', 'url': url, 'caption': alt},
    }
    return {'url': url, 'alt': alt, 'schema_json': _serialize_json_ld(webpage)}
