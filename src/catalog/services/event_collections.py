"""Indexable afisha collections: today, this weekend, theatre, free, ages 3–6…

A collection is a fixed set of public-event filters with its own localized
URL (/tedbirler/hefte-sonu/, /ru/afisha/vyhodnye/, /en/events/weekend/).
Every page is generated from the same public Event reader as the afisha;
nothing here writes data. Collections with fewer than MIN_INDEXABLE_EVENTS
events stay reachable for people but are noindex and absent from sitemaps.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace

from django.core.cache import cache
from django.db.models import Count, Max, Min, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import override

from catalog.services.afisha_urls import AFISHA_LANGUAGES, afisha_language
from catalog.services.event_queries import BAKU, query_public_events
from catalog.services.slugs import build_ascii_slug

MIN_INDEXABLE_EVENTS = 3
CACHE_SECONDS = 15 * 60

DIMENSIONS = ('time', 'category', 'age', 'free', 'district', 'lang')
ALLOWED_PAIRS = frozenset({
    ('time', 'category'), ('time', 'free'), ('category', 'age'), ('category', 'district'),
})
QUICK_TIMES = ('today', 'tomorrow', 'weekend', 'this_week')
MONTHS_AHEAD = 2  # current month + 2 next

TIME_SLUGS = {
    'today': {'az': 'bu-gun', 'ru': 'segodnya', 'en': 'today'},
    'tomorrow': {'az': 'sabah', 'ru': 'zavtra', 'en': 'tomorrow'},
    'weekend': {'az': 'hefte-sonu', 'ru': 'vyhodnye', 'en': 'weekend'},
    'this_week': {'az': 'bu-hefte', 'ru': 'na-nedele', 'en': 'this-week'},
}
MONTH_SLUGS = {
    'az': ('yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avqust', 'sentyabr', 'oktyabr', 'noyabr', 'dekabr'),
    'ru': ('yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avgust', 'sentyabr', 'oktyabr', 'noyabr', 'dekabr'),
    'en': ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'),
}
MONTH_NAMES = {
    'az': ('Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'İyun', 'İyul', 'Avqust', 'Sentyabr', 'Oktyabr', 'Noyabr', 'Dekabr'),
    'ru': ('Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'),
    'en': ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'),
}
RU_MONTH_PREPOSITIONAL = ('январе', 'феврале', 'марте', 'апреле', 'мае', 'июне', 'июле', 'августе', 'сентябре', 'октябре', 'ноябре', 'декабре')
RU_MONTH_GENITIVE = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')

AGE_BANDS = {'0-3': (0, 3), '3-6': (3, 6), '7-12': (7, 12), '12-plus': (12, 17)}
AGE_SLUGS = {
    '0-3': {'az': '0-3-yas', 'ru': '0-3-goda', 'en': 'ages-0-3'},
    '3-6': {'az': '3-6-yas', 'ru': '3-6-let', 'en': 'ages-3-6'},
    '7-12': {'az': '7-12-yas', 'ru': '7-12-let', 'en': 'ages-7-12'},
    '12-plus': {'az': '12-yasdan-boyuk', 'ru': 'ot-12-let', 'en': 'ages-12-plus'},
}
FREE_SLUGS = {'az': 'pulsuz', 'ru': 'besplatnye', 'en': 'free'}
EVENT_LANGUAGES = ('az', 'ru', 'en')
LANG_SLUGS = {
    'az': {'az': 'azerbaycan-dilinde', 'ru': 'rus-dilinde', 'en': 'ingilis-dilinde'},
    'ru': {'az': 'na-azerbajdzhanskom', 'ru': 'na-russkom', 'en': 'na-anglijskom'},
    'en': {'az': 'in-azerbaijani', 'ru': 'in-russian', 'en': 'in-english'},
}
LANG_PHRASES = {
    'az': {'az': 'Azərbaycan dilində', 'ru': 'rus dilində', 'en': 'ingilis dilində'},
    'ru': {'az': 'на азербайджанском языке', 'ru': 'на русском языке', 'en': 'на английском языке'},
    'en': {'az': 'in Azerbaijani', 'ru': 'in Russian', 'en': 'in English'},
}
LANG_CHIPS = {
    'az': {'az': 'Azərbaycan dilində', 'ru': 'Rus dilində', 'en': 'İngilis dilində'},
    'ru': {'az': 'На азербайджанском', 'ru': 'На русском', 'en': 'На английском'},
    'en': {'az': 'In Azerbaijani', 'ru': 'In Russian', 'en': 'In English'},
}
TIME_CHIPS = {
    'az': {'today': 'Bu gün', 'tomorrow': 'Sabah', 'weekend': 'Həftə sonu', 'this_week': 'Bu həftə'},
    'ru': {'today': 'Сегодня', 'tomorrow': 'Завтра', 'weekend': 'Выходные', 'this_week': 'На неделе'},
    'en': {'today': 'Today', 'tomorrow': 'Tomorrow', 'weekend': 'Weekend', 'this_week': 'This week'},
}
TIME_PHRASES = {
    'az': {'today': 'bu gün', 'tomorrow': 'sabah', 'weekend': 'həftə sonu', 'this_week': 'bu həftə'},
    'ru': {'today': 'сегодня', 'tomorrow': 'завтра', 'weekend': 'на выходные', 'this_week': 'на этой неделе'},
    'en': {'today': 'today', 'tomorrow': 'tomorrow', 'weekend': 'this weekend', 'this_week': 'this week'},
}
FREE_CHIPS = {'az': 'Pulsuz', 'ru': 'Бесплатные', 'en': 'Free'}
RESERVED_SLUGS = frozenset({'suggest', 'track'})

EXPIRED = object()  # a month collection whose month is over


@dataclass(frozen=True)
class Collection:
    time: str = ''       # QUICK_TIMES key or 'YYYY-MM'
    category: str = ''   # Category.code
    age: str = ''        # AGE_BANDS key
    free: bool = False
    district: str = ''   # location key (baku_nasimi, xirdalan…)
    lang: str = ''       # language the event is held in

    def dims(self) -> tuple[str, ...]:
        return tuple(dim for dim in DIMENSIONS if getattr(self, dim))

    @property
    def is_month(self) -> bool:
        return bool(self.time) and self.time[:1].isdigit()

    def is_allowed(self) -> bool:
        dims = self.dims()
        return len(dims) == 1 or (len(dims) == 2 and dims in ALLOWED_PAIRS)

    def key(self) -> str:
        return '|'.join(f'{dim}={getattr(self, dim)}' for dim in self.dims())

    def params(self) -> dict:
        params = {}
        if self.time:
            params['upcoming_month' if self.is_month else 'date_filter'] = self.time
        if self.category:
            params['category'] = self.category
        if self.age:
            low, high = AGE_BANDS[self.age]
            params.update(age_from=str(low), age_to=str(high))
        if self.free:
            params['free'] = '1'
        if self.district:
            params['district'] = self.district
        if self.lang:
            params['lang'] = self.lang
        return params

    def without(self, dim: str) -> 'Collection':
        return replace(self, **{dim: False if dim == 'free' else ''})

    def segments(self, language: str, categories=None) -> list[str]:
        language = afisha_language(language)
        out = []
        if self.time:
            out.append(_month_slug(self.time, language) if self.is_month else TIME_SLUGS[self.time][language])
        if self.category:
            out.append(category_slug(self.category, language, categories))
        if self.age:
            out.append(AGE_SLUGS[self.age][language])
        if self.free:
            out.append(FREE_SLUGS[language])
        if self.district:
            out.append(district_slug(self.district))
        if self.lang:
            out.append(LANG_SLUGS[language][self.lang])
        return out

    def path(self, language: str, categories=None) -> str:
        return landing_path(language) + ''.join(f'{segment}/' for segment in self.segments(language, categories))

    def paths(self, categories=None) -> dict[str, str]:
        return {language: self.path(language, categories) for language in AFISHA_LANGUAGES}


def landing_path(language) -> str:
    with override(afisha_language(language)):
        return reverse('events_landing')


# ─── slugs ──────────────────────────────────────────────────────────────────

def _month_slug(value: str, language: str) -> str:
    year, month = value.split('-')
    return f'{MONTH_SLUGS[language][int(month) - 1]}-{year}'


def month_window(now=None) -> list[str]:
    today = (now or timezone.now()).astimezone(BAKU).date()
    months, year, month = [], today.year, today.month
    for _ in range(MONTHS_AHEAD + 1):
        months.append(f'{year:04d}-{month:02d}')
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def category_rows() -> dict:
    from catalog.models import Category
    return {category.code: category for category in Category.objects.filter(deleted_at__isnull=True)}


def category_slug(code: str, language: str, categories=None) -> str:
    categories = categories if categories is not None else category_rows()
    category = categories.get(code)
    fallback = build_ascii_slug(code.replace('_', '-').lower(), fallback='category')
    if category is None:
        return fallback
    name = getattr(category, f'name_{language}', '') or category.name_az or category.name
    return build_ascii_slug(name, fallback=fallback)


def known_districts() -> dict:
    """slug -> location key, for Baku districts and other towns/regions."""
    from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP
    keys = list(BAKU_DISTRICTS_MAP) + [key for key in AZERBAIJAN_REGIONS_MAP if key != 'baku']
    table = {}
    for key in keys:
        table.setdefault(district_slug(key), key)
    return table


def district_slug(key: str) -> str:
    return build_ascii_slug(key.removeprefix('baku_').replace('_', '-'), fallback='district')


def slug_table(language: str, categories=None) -> dict:
    """slug -> (dimension, value) for one language; months are parsed separately."""
    categories = categories if categories is not None else category_rows()
    table = {}
    for key, slugs in TIME_SLUGS.items():
        table[slugs[language]] = ('time', key)
    for key, slugs in AGE_SLUGS.items():
        table[slugs[language]] = ('age', key)
    table[FREE_SLUGS[language]] = ('free', True)
    for code, slug in LANG_SLUGS[language].items():
        table[slug] = ('lang', code)
    for code in sorted(categories, key=lambda code: (categories[code].order, code)):
        table.setdefault(category_slug(code, language, categories), ('category', code))
    for slug, key in known_districts().items():
        table.setdefault(slug, ('district', key))
    return table


_MONTH_RE = re.compile(r'^([a-z]+)-(\d{4})$')


def _parse_month(segment: str, language: str):
    match = _MONTH_RE.match(segment)
    if not match or match.group(1) not in MONTH_SLUGS[language]:
        return None
    return f'{match.group(2)}-{MONTH_SLUGS[language].index(match.group(1)) + 1:02d}'


def resolve_segments(segments, language, *, now=None, categories=None):
    """URL segments -> Collection, EXPIRED (month is over) or None (404).

    Another language's spelling is accepted; the view compares the canonical
    path and redirects.
    """
    language = afisha_language(language)
    categories = categories if categories is not None else category_rows()
    order = [language] + [code for code in AFISHA_LANGUAGES if code != language]
    tables = {}
    values = {}
    for segment in segments:
        if not segment or segment in RESERVED_SLUGS:
            return None
        hit = None
        for code in order:
            month = _parse_month(segment, code)
            if month:
                hit = ('time', month)
                break
            if code not in tables:
                tables[code] = slug_table(code, categories)
            if segment in tables[code]:
                hit = tables[code][segment]
                break
        if hit is None or hit[0] in values:
            return None
        values[hit[0]] = hit[1]
    if not values:
        return None
    collection = Collection(**values)
    if not collection.is_allowed():
        return None
    if collection.is_month:
        window = month_window(now)
        if collection.time < window[0]:
            return EXPIRED
        if collection.time not in window:
            return None
    return collection


def collection_for_query(params, *, categories=None) -> Collection | None:
    """A clean afisha query that equals one collection (old ?date_filter= links)."""
    get = lambda key: str(params.get(key) or '').strip()
    noise = {'view': {'', 'list'}, 'sort': {'', 'date'}}
    handled = {'date_filter', 'category', 'free', 'district', 'lang', 'age_from', 'age_to', 'page'}
    for key in params:
        value = get(key)
        if key in noise:
            if value not in noise[key]:
                return None
        elif key not in handled and value:
            return None
    values = {}
    if get('date_filter'):
        if get('date_filter') not in QUICK_TIMES:
            return None
        values['time'] = get('date_filter')
    if get('category'):
        values['category'] = get('category')
    if get('free'):
        if get('free') != '1':
            return None
        values['free'] = True
    if get('district'):
        if get('district') not in known_districts().values():
            return None
        values['district'] = get('district')
    if get('lang'):
        if get('lang') not in EVENT_LANGUAGES:
            return None
        values['lang'] = get('lang')
    if get('age_from') or get('age_to'):
        band = next((key for key, (low, high) in AGE_BANDS.items()
                     if (get('age_from'), get('age_to')) == (str(low), str(high))), None)
        if band is None:
            return None
        values['age'] = band
    if not values:
        return None
    collection = Collection(**values)
    if collection.category:
        categories = categories if categories is not None else category_rows()
        if collection.category not in categories:
            return None
    return collection if collection.is_allowed() else None


# ─── counts (cached snapshot of every candidate collection) ─────────────────

def collection_queryset(collection: Collection, *, now=None):
    return query_public_events(collection.params(), now=now)


def _stats(collection, now):
    row = collection_queryset(collection, now=now).order_by().aggregate(n=Count('pk'), last=Max('updated_at'))
    return int(row['n'] or 0), row['last']


def _version(now) -> str:
    from catalog.models import Category, Event
    events = Event.objects.order_by().aggregate(n=Count('pk'), last=Max('updated_at'))
    categories = Category.objects.order_by().aggregate(n=Count('pk'), last=Max('updated_at'))
    bucket = int(now.timestamp() // CACHE_SECONDS)
    stamp = lambda value: value.isoformat() if value else '-'
    return (f"{bucket}:{events['n']}:{stamp(events['last'])}:"
            f"{categories['n']}:{stamp(categories['last'])}")


def snapshot(now=None) -> dict:
    """Every candidate collection -> (event count, last update). Cached ~15 min."""
    now = now or timezone.now()
    key = f'afisha-collections:v1:{_version(now)}'
    cached = cache.get(key)
    if cached is not None:
        return {Collection(**values): (count, last) for values, count, last in cached}

    base = query_public_events({}, now=now).order_by()
    category_codes = sorted({code for code in base.values_list('category_id', flat=True) if code})
    known = set(known_districts().values())
    districts = sorted({value for value in base.values_list('venue_snapshot__district', flat=True)
                        if isinstance(value, str) and value in known})
    singles = ([Collection(time=key) for key in QUICK_TIMES]
               + [Collection(time=month) for month in month_window(now)]
               + [Collection(category=code) for code in category_codes]
               + [Collection(age=key) for key in AGE_BANDS]
               + [Collection(free=True)]
               + [Collection(district=key) for key in districts]
               + [Collection(lang=code) for code in EVENT_LANGUAGES])
    result = {collection: _stats(collection, now) for collection in singles}
    strong = [collection for collection in singles if result[collection][0] >= MIN_INDEXABLE_EVENTS]
    for first_dim, second_dim in sorted(ALLOWED_PAIRS):
        for first in (c for c in strong if c.dims() == (first_dim,)):
            for second in (c for c in strong if c.dims() == (second_dim,)):
                combo = replace(first, **{second_dim: getattr(second, second_dim)})
                result[combo] = _stats(combo, now)
    cache.set(key, [(asdict(c), count, last) for c, (count, last) in result.items()], CACHE_SECONDS)
    return result


def _hub_total(now):
    return query_public_events({}, now=now).order_by().count()


def _parents(collection):
    """Broader pages this one narrows. Time is a search intent of its own, so a
    date page is never a duplicate of the undated hub."""
    dims = collection.dims()
    if len(dims) == 1:
        return [] if dims == ('time',) else [None]
    return [collection.without(dim) for dim in dims if dim != 'time']


def _is_distinct(collection, count, snap, total) -> bool:
    """A page that lists exactly the same events as a broader one is a duplicate."""
    for parent in _parents(collection):
        parent_count = total if parent is None else (snap.get(parent, (None,))[0])
        if parent_count is not None and count >= parent_count:
            return False
    return True


def count_for(collection, *, now=None, snap=None) -> int:
    snap = snap if snap is not None else snapshot(now)
    if collection in snap:
        return snap[collection][0]
    return _stats(collection, now or timezone.now())[0]


def is_indexable(collection, *, now=None, snap=None) -> bool:
    snap = snap if snap is not None else snapshot(now)
    count = count_for(collection, now=now, snap=snap)
    return count >= MIN_INDEXABLE_EVENTS and _is_distinct(collection, count, snap, _hub_total(now))


def _rank(collection) -> tuple:
    dims = collection.dims()
    return (len(dims), DIMENSIONS.index(dims[0]), collection.is_month)


def indexable_collections(now=None) -> list:
    snap = snapshot(now)
    total = _hub_total(now)
    rows = [(c, count, last) for c, (count, last) in snap.items()
            if count >= MIN_INDEXABLE_EVENTS and _is_distinct(c, count, snap, total)]
    return sorted(rows, key=lambda row: (_rank(row[0]), -row[1], row[0].key()))


# ─── labels and copy ────────────────────────────────────────────────────────

def category_name(code, language, categories=None) -> str:
    categories = categories if categories is not None else category_rows()
    category = categories.get(code)
    if category is None:
        return code
    return (getattr(category, f'name_{language}', '') or category.name_az or category.name or code).strip()


def district_name(key, language) -> str:
    from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP
    if key in BAKU_DISTRICTS_MAP:
        name = BAKU_DISTRICTS_MAP[key].get(language) or key
        return {'az': f'{name} rayonu', 'en': f'{name} District'}.get(language, f'{name} район')
    return AZERBAIJAN_REGIONS_MAP.get(key, {}).get(language, key)


def _age_phrase(band, language):
    low, high = AGE_BANDS[band]
    if language == 'az':
        return '12 yaşdan böyük' if band == '12-plus' else f'{low}–{high} yaş'
    if language == 'en':
        return 'ages 12+' if band == '12-plus' else f'ages {low}–{high}'
    return {'0-3': 'до 3 лет', '12-plus': 'от 12 лет'}.get(band, f'{low}–{high} лет')


def _month_parts(value):
    year, month = value.split('-')
    return int(year), int(month)


def _time_phrase(time, language):
    if not time:
        return ''
    if time[:1].isdigit():
        year, month = _month_parts(time)
        if language == 'ru':
            return f'в {RU_MONTH_PREPOSITIONAL[month - 1]} {year}'
        if language == 'en':
            return f'in {MONTH_NAMES["en"][month - 1]} {year}'
        return f'{MONTH_NAMES["az"][month - 1]} {year}'
    return TIME_PHRASES[language][time]


def _capital(text):
    return text[:1].upper() + text[1:]


def short_label(collection, language, categories=None) -> str:
    """Chip / breadcrumb label: «Выходные», «Спорт · 3–6 лет»."""
    language = afisha_language(language)
    parts = []
    if collection.time:
        if collection.is_month:
            year, month = _month_parts(collection.time)
            parts.append(f'{MONTH_NAMES[language][month - 1]} {year}')
        else:
            parts.append(TIME_CHIPS[language][collection.time])
    if collection.category:
        parts.append(category_name(collection.category, language, categories))
    if collection.age:
        parts.append(_capital(_age_phrase(collection.age, language)))
    if collection.free:
        parts.append(FREE_CHIPS[language])
    if collection.district:
        parts.append(district_name(collection.district, language))
    if collection.lang:
        parts.append(LANG_CHIPS[language][collection.lang])
    return ' · '.join(parts)


def heading(collection, language, categories=None) -> str:
    """The H1, phrased the way parents search."""
    language = afisha_language(language)
    c = collection
    category = category_name(c.category, language, categories) if c.category else ''
    district = district_name(c.district, language) if c.district else ''
    time = _time_phrase(c.time, language)
    if language in ('ru', 'en'):
        if c.dims() == ('time',):
            return f'Детская афиша Баку {time}' if language == 'ru' else f'Kids’ events in Baku {time}'
        if language == 'ru':
            if category:
                subject = f'{category} для детей' + (f' {_age_phrase(c.age, "ru")}' if c.age else '')
            elif c.age:
                subject = f'Мероприятия для детей {_age_phrase(c.age, "ru")}'
            elif c.free:
                subject = 'Бесплатные детские мероприятия'
            else:
                subject = 'Детские мероприятия'
            where = f' — {district}' if district else ' в Баку'
        else:
            if category:
                subject = f'{category} for kids' + (f', {_age_phrase(c.age, "en")}' if c.age else '')
            elif c.age:
                subject = f'Events for kids, {_age_phrase(c.age, "en")}'
            elif c.free:
                subject = 'Free kids’ events'
            else:
                subject = 'Kids’ events'
            where = f' — {district}' if district else ' in Baku'
        text = subject + (f' {LANG_PHRASES[language][c.lang]}' if c.lang else '') + where
        return f'{text} {time}'.strip()
    # az: «İdman: Bakıda həftə sonu uşaqlar üçün tədbirlər»
    prefix = f'{category}: ' if category else ''
    month = f'{time}: ' if c.is_month else ''
    quick = f'{time} ' if c.time and not c.is_month else ''
    where = '' if district else 'Bakıda '
    lang = f'{LANG_PHRASES["az"][c.lang]} ' if c.lang else ''
    if c.free:
        subject = 'pulsuz uşaq tədbirləri'
    elif c.age:
        subject = f'{_age_phrase(c.age, "az")} uşaqlar üçün tədbirlər'
    else:
        subject = 'uşaqlar üçün tədbirlər'
    text = _capital(f'{where}{quick}{lang}{subject}')
    if district:
        text += f' — {district}'
    return f'{prefix}{month}{text}'


def seo_title(collection, language, categories=None) -> str:
    from catalog.services.seo import build_branded_seo_title
    return build_branded_seo_title(heading(collection, language, categories))


def events_word(count, language) -> str:
    if language == 'az':
        return f'{count} tədbir'
    if language == 'en':
        return f'{count} event' + ('' if count == 1 else 's')
    from catalog.services.event_afisha import ru_events_label
    return ru_events_label(count)


def meta_description(title, language, count) -> str:
    language = afisha_language(language)
    if language == 'az':
        text = (f'{title}: {events_word(count, "az")}. Tarixlər, yaş, qiymət və ünvanlar bir yerdə. '
                'Siyahı avtomatik yenilənir.') if count else f'{title}. Yeni tədbirlər əlavə olunduqca siyahı yenilənir.'
    elif language == 'en':
        text = (f'{title}: {events_word(count, "en")}. Dates, ages, prices and venues in one place. '
                'Updated automatically.') if count else f'{title}. The list updates as new events are added.'
    else:
        text = (f'{title}: {events_word(count, "ru")}. Даты, возраст, цены и адреса в одном месте. '
                'Подборка обновляется автоматически.') if count else f'{title}. Подборка пополняется по мере появления событий.'
    return Truncator(text).chars(158, truncate='…')


HERO_INTRO = {
    'az': 'Yalnız aktual tədbirlər: keçmişlər siyahıdan özü çıxır. Tarixi, yaşı və yeri müqayisə edin.',
    'ru': 'Только актуальные события — прошедшие исчезают сами. Сравнивайте даты, возраст и место.',
    'en': 'Only events you can still attend — past ones drop off automatically. Compare dates, ages and venues.',
}


def _format_moment(value, language):
    local = value.astimezone(BAKU)
    hm = local.strftime('%H:%M')
    if language == 'ru':
        return f'{local.day} {RU_MONTH_GENITIVE[local.month - 1]} в {hm}'
    if language == 'en':
        return f'{MONTH_NAMES["en"][local.month - 1]} {local.day} at {hm}'
    return f'{local.day} {MONTH_NAMES["az"][local.month - 1].lower()}, saat {hm}'


def format_day(value, language) -> str:
    local = value.astimezone(BAKU)
    if language == 'ru':
        return f'{local.day} {RU_MONTH_GENITIVE[local.month - 1]} {local.year}'
    if language == 'en':
        return f'{MONTH_NAMES["en"][local.month - 1]} {local.day}, {local.year}'
    return f'{local.day} {MONTH_NAMES["az"][local.month - 1].lower()} {local.year}'


def _venue(event, language):
    label = (getattr(event, 'venue_label', '') or '').strip()
    if label:
        return label
    place = getattr(event, 'related_place', None) if getattr(event, 'related_place_id', None) else None
    if place is not None and hasattr(place, 'name_i18n'):
        return str(place.name_i18n(language) or '').strip()
    return ''


def collection_facts(queryset, *, now, language) -> dict:
    """Numbers for the answer card and FAQ, read from the collection's own events."""
    from catalog.services.event_presentation import LEGACY_FREE_PATTERN
    language = afisha_language(language)
    base = queryset.order_by()
    total = base.count()
    free = base.filter(Q(price_mode='free') | Q(price_mode='legacy', price_text__iregex=LEGACY_FREE_PATTERN)).count()
    ages = base.aggregate(low=Min('age_from'), high=Max('age_to'))
    upcoming = queryset.filter(start_datetime__gt=now).order_by('start_datetime', 'pk').first()
    nearest = None
    if upcoming is not None:
        nearest = {'name': upcoming.name_i18n(language), 'when': _format_moment(upcoming.start_datetime, language),
                   'venue': _venue(upcoming, language), 'url': upcoming.get_absolute_url()}
    return {'total': total, 'free': free, 'running': base.filter(start_datetime__lte=now).count(),
            'age_low': ages['low'], 'age_high': ages['high'], 'nearest': nearest,
            'updated': format_day(now, language)}


def _age_range(low, high, language):
    if low is None and high is None:
        return ''
    if language == 'ru':
        return ' '.join(part for part in (f'от {low}' if low is not None else '', f'до {high}' if high is not None else '') if part) + ' лет'
    if language == 'en':
        return f'{low}–{high}' if low is not None and high is not None else (f'{low}+' if low is not None else f'up to {high}')
    return (f'{low}–{high} yaş' if low is not None and high is not None
            else (f'{low} yaşdan' if low is not None else f'{high} yaşa qədər'))


def answer_text(title, facts, language) -> str:
    """2–3 factual sentences: the paragraph search engines and AI assistants quote."""
    language = afisha_language(language)
    total, free, nearest = facts['total'], facts['free'], facts['nearest']
    ages = _age_range(facts['age_low'], facts['age_high'], language)
    if not total:
        return {
            'az': f'«{title}» seçimində hazırda tədbir yoxdur. Aşağıda afişanın ən yaxın tədbirləri var; yeniləri burada avtomatik görünəcək.',
            'ru': f'В подборке «{title}» сейчас нет мероприятий. Ниже — ближайшие события афиши; новые появятся здесь автоматически.',
            'en': f'There are no events in “{title}” right now. The nearest events are below; new ones appear here automatically.',
        }[language]
    venue = f', {nearest["venue"]}' if nearest and nearest['venue'] else ''
    if language == 'ru':
        free_part = ', все бесплатные' if free == total else (f', из них бесплатных — {free}' if free else '')
        out = [f'{title}: {events_word(total, "ru")}{free_part}.']
        if nearest:
            out.append(f'Ближайшее — «{nearest["name"]}», {nearest["when"]}{venue}.')
        if ages:
            out.append(f'Возраст участников — {ages}.')
    elif language == 'en':
        free_part = ', all free' if free == total else (f', {free} of them free' if free else '')
        out = [f'{title}: {events_word(total, "en")}{free_part}.']
        if nearest:
            out.append(f'Next up: “{nearest["name"]}”, {nearest["when"]}{venue}.')
        if ages:
            out.append(f'Suitable ages: {ages}.')
    else:
        free_part = ', hamısı pulsuz' if free == total else (f', onlardan {free} pulsuz' if free else '')
        out = [f'{title}: {events_word(total, "az")}{free_part}.']
        if nearest:
            out.append(f'Ən yaxını — «{nearest["name"]}», {nearest["when"]}{venue}.')
        if ages:
            out.append(f'Uşaqların yaşı — {ages}.')
    return ' '.join(out)


def faq_items(collection, title, facts, language) -> list:
    """Questions parents ask, answered only from the collection's own data."""
    language = afisha_language(language)
    total, free = facts['total'], facts['free']
    ages = _age_range(facts['age_low'], facts['age_high'], language)
    ask_free = not (collection is not None and collection.free)
    hub = collection is None
    items = []
    if language == 'ru':
        items.append({'q': 'Сколько детских мероприятий сейчас в афише Баку?' if hub else f'Сколько мероприятий в подборке «{title}»?',
                      'a': f'Сейчас {events_word(total, "ru")}. Список обновляется автоматически: прошедшие события исчезают, новые появляются после модерации. Проверено {facts["updated"]}.'})
        if ask_free:
            items.append({'q': 'Есть ли бесплатные мероприятия?',
                          'a': (f'Да, бесплатных — {free}. Все бесплатные события афиши собраны в отдельной подборке.' if free
                                else 'Здесь бесплатных сейчас нет. Загляните в подборку бесплатных мероприятий — она обновляется каждый день.')})
        if ages:
            items.append({'q': 'Для какого возраста эти мероприятия?',
                          'a': f'Возраст указан в каждой карточке; в этой подборке — {ages}. Подобрать событие под возраст ребёнка можно в фильтрах афиши.'})
        items.append({'q': 'Как записаться или купить билет?',
                      'a': 'Откройте карточку мероприятия: там указан способ записи — сайт организатора, WhatsApp или звонок. KidsMap не продаёт билеты и не берёт комиссию; цену и условия уточняйте у организатора.'})
    elif language == 'en':
        items.append({'q': 'How many kids’ events are on in Baku right now?' if hub else f'How many events are in “{title}”?',
                      'a': f'Right now: {events_word(total, "en")}. The list updates automatically — past events drop off and new ones appear after moderation. Checked on {facts["updated"]}.'})
        if ask_free:
            items.append({'q': 'Are there free events?',
                          'a': (f'Yes — {free} free. All free events are also collected on a separate page.' if free
                                else 'Not in this selection right now. See the free events page — it is updated daily.')})
        if ages:
            items.append({'q': 'What ages are these events for?',
                          'a': f'Each card shows the age range; in this selection: {ages}. You can match events to your child’s age with the afisha filters.'})
        items.append({'q': 'How do I sign up or buy a ticket?',
                      'a': 'Open the event card: it shows how to register — the organizer’s website, WhatsApp or a phone call. KidsMap does not sell tickets or charge fees; confirm the price and conditions with the organizer.'})
    else:
        items.append({'q': 'Hazırda Bakıda uşaqlar üçün neçə tədbir var?' if hub else f'«{title}» seçimində neçə tədbir var?',
                      'a': f'Hazırda {events_word(total, "az")}. Siyahı avtomatik yenilənir: keçmiş tədbirlər çıxır, yeniləri moderasiyadan sonra əlavə olunur. Yoxlanılıb: {facts["updated"]}.'})
        if ask_free:
            items.append({'q': 'Pulsuz tədbirlər varmı?',
                          'a': (f'Bəli, {free} pulsuz tədbir var. Bütün pulsuz tədbirlər ayrıca seçimdə toplanıb.' if free
                                else 'Bu seçimdə hazırda pulsuz tədbir yoxdur. Pulsuz tədbirlər seçiminə baxın — hər gün yenilənir.')})
        if ages:
            items.append({'q': 'Tədbirlər hansı yaş üçündür?',
                          'a': f'Yaş hər kartda göstərilib; bu seçimdə — {ages}. Uşağın yaşına uyğun tədbiri afişanın filtrləri ilə seçə bilərsiniz.'})
        items.append({'q': 'Necə qeydiyyatdan keçmək və ya bilet almaq olar?',
                      'a': 'Tədbirin kartını açın: qeydiyyat üsulu orada göstərilib — təşkilatçının saytı, WhatsApp və ya zəng. KidsMap bilet satmır və komissiya almır; qiyməti və şərtləri təşkilatçıdan dəqiqləşdirin.'})
    return items


# ─── links between collections ──────────────────────────────────────────────

_ICONS = {'category': 'interests', 'age': 'child_care', 'free': 'redeem', 'district': 'location_on', 'lang': 'translate'}
_TIME_ICONS = {'today': 'today', 'tomorrow': 'wb_sunny', 'weekend': 'weekend', 'this_week': 'date_range'}


def _icon(collection):
    dims = collection.dims()
    if dims == ('time',):
        return _TIME_ICONS.get(collection.time, 'calendar_month')
    return _ICONS.get(dims[-1], 'event')


def link(collection, count, language, categories=None) -> dict:
    return {'url': collection.path(language, categories), 'label': short_label(collection, language, categories),
            'count': count, 'icon': _icon(collection), 'key': collection.key()}


def related_links(collection, language, *, now=None, limit=10, categories=None) -> list:
    """Indexable neighbours of a collection, most useful first."""
    categories = categories if categories is not None else category_rows()
    good = {c: count for c, count, _last in indexable_collections(now) if c != collection}
    picks = []

    def add(candidates):
        for c in sorted(candidates, key=lambda c: (-good[c], c.key())):
            if c not in picks:
                picks.append(c)

    if collection.time:
        add([c for c in good if c.time == collection.time and len(c.dims()) == 2])
        add([c for c in good if c.dims() == ('time',) and c.is_month == collection.is_month])
    if collection.category:
        add([c for c in good if c.category == collection.category])
        add([c for c in good if c.dims() == ('category',)])
    for dim in ('age', 'free', 'district', 'lang'):
        if getattr(collection, dim):
            add([c for c in good if c.dims() == (dim,)])
    add([c for c in good if c.dims() == ('time',)])
    add([c for c in good if c.dims() == ('free',)])
    add([c for c in good if c.dims() == ('category',)])
    return [link(c, good[c], language, categories) for c in picks[:limit]]


def hub_links(language, *, now=None, limit=18, categories=None) -> list:
    """Collections linked from the main afisha page (single dimension, indexable)."""
    categories = categories if categories is not None else category_rows()
    rows = [(c, count) for c, count, _last in indexable_collections(now) if len(c.dims()) == 1]
    return [link(c, count, language, categories) for c, count in rows[:limit]]


def quick_urls(collection, language, *, now=None, categories=None):
    """Date chips on a collection page keep its other filter when such a page exists."""
    categories = categories if categories is not None else category_rows()
    snap = snapshot(now)
    rest = collection.without('time') if collection.time else collection
    urls = {'all': rest.path(language, categories) if rest.dims() else landing_path(language)}
    counts = {'total': count_for(rest, now=now, snap=snap) if rest.dims() else None}
    for key in QUICK_TIMES:
        target = replace(rest, time=key)
        if not target.is_allowed():
            target = Collection(time=key)
        urls[key] = target.path(language, categories)
        counts[key] = count_for(target, now=now, snap=snap)
    return urls, counts


def landing_quick_urls(language) -> dict:
    urls = {key: Collection(time=key).path(language) for key in QUICK_TIMES}
    urls['all'] = landing_path(language)
    return urls
