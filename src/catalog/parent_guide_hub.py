"""The /parents/ hub: every parent guide, grouped by rubric, plus guide-to-guide links.

Structure for search engines and people alike:
Home → /parents/ (this hub) → /parents/<slug>/ (a guide) → /catalog/… and the afisha.
Rubrics without guides are not shown; a new guide only needs a GUIDE_RUBRICS entry.
"""
from datetime import date

from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.translation import override

from catalog.parent_guide_content import GUIDE_PAGES

# Order is the order on the hub.
RUBRICS = (
    {'key': 'outings', 'icon': 'explore',
     'title': {'az': 'Hara getmək', 'ru': 'Куда пойти', 'en': 'Where to go'},
     'text': {'az': 'Ailəvi gün üçün ideyalar: gəzinti, oyun və yeni təəssüratlar.',
              'ru': 'Идеи для семейного дня: прогулки, игры и новые впечатления.',
              'en': 'Ideas for a family day: walks, play and something new.'}},
    {'key': 'sport', 'icon': 'sports_soccer',
     'title': {'az': 'İdman və bölmələr', 'ru': 'Спорт и секции', 'en': 'Sports and clubs'},
     'text': {'az': 'Uşaq üçün idman növünü və ilk məşqi necə seçmək olar.',
              'ru': 'Как выбрать вид спорта и первую тренировку для ребёнка.',
              'en': 'How to choose a sport and a first class for your child.'}},
    {'key': 'age', 'icon': 'child_care',
     'title': {'az': 'Yaşa görə', 'ru': 'По возрасту', 'en': 'By age'},
     'text': {'az': 'Uşağın yaşına uyğun məsləhətlər.',
              'ru': 'Советы под возраст ребёнка.',
              'en': 'Advice for your child’s age.'}},
    {'key': 'museums-parks', 'icon': 'park',
     'title': {'az': 'Muzeylər və parklar', 'ru': 'Музеи и парки', 'en': 'Museums and parks'},
     'text': {'az': 'Açıq havada gəzinti və uşaqlar üçün maraqlı muzeylər.',
              'ru': 'Прогулки на свежем воздухе и музеи, интересные детям.',
              'en': 'Fresh-air walks and museums children enjoy.'}},
)
GUIDE_RUBRICS = {
    'baku-with-kids': 'outings',
    'play-centers': 'outings',
    'sport': 'sport',
    'museums': 'museums-parks',
    'parks': 'museums-parks',
}
DEFAULT_RUBRIC = 'outings'
RELATED_LIMIT = 4

HUB_COPY = {
    'az': {
        'title': 'Bakıda valideynlər üçün bələdçilər',
        'seo_title': 'Valideynlər üçün bələdçilər: Bakıda uşaqla hara getməli',
        'meta_description': ('KidsMap bələdçiləri: Bakıda uşaqla hara getməli, parklar, muzeylər, oyun mərkəzləri '
                             'və idman bölmələri. Praktik məsləhətlər və məkanlar.'),
        'eyebrow': 'Valideynlər üçün',
        'lead': ('Qısa və praktik bələdçilər: uşaqla hara getmək, bölməni necə seçmək, harada gəzmək və nəyə baxmaq. '
                 'Hər bələdçi kataloqdakı məkanlara aparır.'),
        'crumb': 'Valideynlər üçün', 'rubrics_label': 'Mövzular',
        'guides_word': 'bələdçi', 'updated': 'Yenilənib', 'read': 'Oxu',
        'related_title': 'Mövzu üzrə digər bələdçilər', 'all_guides': 'Bütün bələdçilər',
        'afisha_eyebrow': 'Afişa', 'catalog_title': 'Bütün məkanlar kataloqda',
        'catalog_text': 'Dərnəklər, bölmələr, parklar və mərkəzlər — rayon və yaşa görə filtr.',
    },
    'ru': {
        'title': 'Гиды для родителей в Баку',
        'seo_title': 'Гиды для родителей: куда пойти с ребёнком в Баку',
        'meta_description': ('Гиды KidsMap для родителей в Баку: куда сходить с ребёнком, парки, музеи, игровые центры '
                             'и спортивные секции. Практичные советы и места.'),
        'eyebrow': 'Родителям',
        'lead': ('Короткие практичные гиды: куда пойти с ребёнком, как выбрать секцию, где погулять и что посмотреть. '
                 'Каждый гид ведёт к местам в каталоге.'),
        'crumb': 'Родителям', 'rubrics_label': 'Темы',
        'guides_word': '', 'updated': 'Обновлено', 'read': 'Читать',
        'related_title': 'Ещё гиды по теме', 'all_guides': 'Все гиды',
        'afisha_eyebrow': 'Афиша', 'catalog_title': 'Все места в каталоге',
        'catalog_text': 'Кружки, секции, парки и центры — с фильтрами по району и возрасту.',
    },
    'en': {
        'title': 'Guides for parents in Baku',
        'seo_title': 'Parent guides: things to do with kids in Baku',
        'meta_description': ('KidsMap guides for parents in Baku: where to go with children, parks, museums, play centres '
                             'and sports clubs. Practical tips and places to visit.'),
        'eyebrow': 'For parents',
        'lead': ('Short, practical guides: where to go with your child, how to choose a club, where to walk and what to see. '
                 'Every guide links to places in the directory.'),
        'crumb': 'For parents', 'rubrics_label': 'Topics',
        'guides_word': 'guides', 'updated': 'Updated', 'read': 'Read',
        'related_title': 'More guides on this topic', 'all_guides': 'All guides',
        'afisha_eyebrow': 'Events', 'catalog_title': 'Every place in the directory',
        'catalog_text': 'Clubs, classes, parks and centres — filter by district and age.',
    },
}

AFISHA_TEXT = {
    'az': 'Tamaşalar, ustad dərsləri və bayramlar — yaxın günlərdə Bakıda nə var.',
    'ru': 'Спектакли, мастер-классы и праздники — что идёт в Баку в ближайшие дни.',
    'en': 'Shows, workshops and celebrations — what’s on in Baku in the coming days.',
}


def _language(language):
    code = str(language or 'az').split('-', 1)[0]
    return code if code in HUB_COPY else 'az'


def guides_word(count, language):
    if language == 'ru':
        from catalog.services.event_afisha import ru_plural
        return f'{count} ' + ru_plural(count, 'гид', 'гида', 'гидов')
    if language == 'en':
        return f'{count} guide' + ('' if count == 1 else 's')
    return f'{count} bələdçi'


def guide_card(slug, language):
    definition = GUIDE_PAGES[slug]
    copy = definition['translations'].get(language)
    if copy is None:
        return None
    with override(language):
        url = reverse('parent_guide', kwargs={'slug': slug})
    image = definition.get('hero_image_small') or definition['hero_image']
    return {
        'slug': slug,
        'url': url,
        'title': copy['title'],
        'eyebrow': copy.get('eyebrow', ''),
        'lead': Truncator(copy.get('lead', '')).chars(150, truncate='…'),
        'image': static(image),
        'image_alt': copy.get('hero_alt', ''),
        'updated': date.fromisoformat(definition['updated']),
        'rubric': GUIDE_RUBRICS.get(slug, DEFAULT_RUBRIC),
    }


def all_cards(language):
    language = _language(language)
    cards = [guide_card(slug, language) for slug in GUIDE_PAGES]
    return [card for card in cards if card]


def rubrics(language, cards=None):
    """Rubrics that have at least one guide, each with its cards in hub order."""
    language = _language(language)
    cards = cards if cards is not None else all_cards(language)
    out = []
    for rubric in RUBRICS:
        members = [card for card in cards if card['rubric'] == rubric['key']]
        if members:
            out.append({'key': rubric['key'], 'icon': rubric['icon'], 'title': rubric['title'][language],
                        'text': rubric['text'][language], 'guides': members})
    return out


def related_guides(slug, language, limit=RELATED_LIMIT):
    """The guide's own related_slug first, then the same rubric, then the freshest others."""
    language = _language(language)
    cards = [card for card in all_cards(language) if card['slug'] != slug]
    rubric = GUIDE_RUBRICS.get(slug, DEFAULT_RUBRIC)
    preferred = GUIDE_PAGES.get(slug, {}).get('related_slug')
    cards.sort(key=lambda card: (card['slug'] != preferred, card['rubric'] != rubric,
                                 -card['updated'].toordinal(), card['slug']))
    return cards[:limit]


def afisha_card(slug, language):
    """A matching afisha collection for a guide (or for the hub). None when events are off."""
    from catalog.services.features import is_events_section_enabled
    if not is_events_section_enabled():
        return None
    from catalog.services import event_collections as ec
    language = _language(language)
    categories = ec.category_rows()
    collection = ec.Collection(time='weekend')
    if slug == 'sport' and 'SPRT' in categories:
        collection = ec.Collection(category='SPRT')
    return {'url': collection.path(language, categories), 'title': ec.heading(collection, language, categories),
            'text': AFISHA_TEXT[language], 'eyebrow': HUB_COPY[language]['afisha_eyebrow']}


def last_updated(cards):
    return max((card['updated'] for card in cards), default=None)
