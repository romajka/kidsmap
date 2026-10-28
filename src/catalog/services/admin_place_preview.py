"""Read-only staff presentation of a saved Place or its submitted candidate.

Do not use the public detail controller here: it filters unpublished content,
tracks views and can refresh rating statistics. This module only reads.
"""
import copy
from types import SimpleNamespace
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from catalog.models import Place, PlacePhoto, PricingPlan, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.place_schedule import build_schedule_rows
from catalog.services.pricing_plans import PRICING_STORAGE_FIELDS, format_price_amount

LANGUAGES = ('az', 'ru', 'en')
PLAN_LABELS = {
    'lesson_format': _('Формат занятий'), 'age_from': _('Возраст от'), 'age_to': _('Возраст до'),
    'product_type': _('Тип тарифа'), 'charge_role': _('Назначение платежа'),
    'billing_mode': _('Модель оплаты'), 'billing_interval': _('Период оплаты'),
    'billing_interval_count': _('Количество периодов'), 'billing_cycles': _('Количество платежей'),
    'price_kind': _('Тип цены'), 'price': _('Цена'), 'price_min': _('Цена от'), 'price_max': _('Цена до'),
    'currency': _('Валюта'), 'quantity': _('Количество занятий'), 'quantity_unit': _('Единица количества'),
    'sessions_per_week': _('Занятий в неделю'), 'sessions_per_month': _('Занятий в месяц'),
    'is_unlimited': _('Безлимит'), 'validity_interval': _('Период действия'),
    'validity_interval_count': _('Количество периодов действия'), 'valid_from': _('Действует с'),
    'valid_until': _('Действует до'), 'audience_type': _('Для кого'),
    'min_people': _('Минимум участников'), 'max_people': _('Максимум участников'),
    'day_type': _('Дни посещения'), 'is_required': _('Обязательный платёж'),
    'is_trial': _('Пробное занятие'), 'is_active': _('Тариф активен'),
    'sort_order': _('Порядок'), 'source_url': _('Источник цены'), 'verified_at': _('Цена проверена'),
}


def external_link(value):
    value = str(value or '').strip()
    if not value:
        return ''
    try:
        URLValidator(schemes=['http', 'https'])(value)
    except ValidationError:
        return ''
    return value


def _field_rows(model, values, names, *, labels=None):
    rows = []
    for name in names:
        field = model._meta.get_field(name)
        value = values.get(name)
        link = ''
        if value is None or value == '':
            value = _('Не указано')
        elif field.get_internal_type() == 'BooleanField':
            value = _('Да') if value else _('Нет')
        elif field.choices:
            value = dict(field.flatchoices).get(value, value)
        elif field.get_internal_type() == 'DecimalField':
            value = format_price_amount(value)
        if name in {'website', 'source_url'}:
            link = external_link(value)
        rows.append({'label': (labels or {}).get(name, field.verbose_name), 'value': str(value), 'url': link})
    return rows


def _translations(values, fields):
    return [{'label': label, 'values': [{'language': lang, 'value': values.get(f'{name}_{lang}', '')}
        for lang in LANGUAGES]} for name, label in fields]


def _photo(name, caption, role, *, gallery=False):
    field = PlacePhoto._meta.get_field('image') if gallery else Place._meta.get_field('photo')
    url = ''
    if name:
        try:
            if field.storage.exists(str(name)):
                url = field.storage.url(str(name))
        except (OSError, ValueError):
            pass
    return {'url': url, 'caption': caption, 'role': role, 'missing': bool(name and not url)}


def _plan(values, language):
    localized = _translations(values, [('title', _('Название тарифа')), ('conditions', _('Условия тарифа'))])
    primary = ('product_type', 'charge_role', 'price_kind', 'price', 'price_min', 'price_max', 'currency',
               'billing_mode', 'billing_interval', 'billing_interval_count', 'billing_cycles', 'is_active')
    primary += ('is_required', 'is_trial')
    secondary = [name for name in PRICING_STORAGE_FIELDS
        if name not in primary and not name.startswith(('title_', 'conditions_')) and (name != 'verified_at' or name in values)]
    title = values.get(f'title_{language}') or next((values.get(f'title_{lang}') for lang in LANGUAGES if values.get(f'title_{lang}')), '')
    return {'title': title or _('Тариф'), 'rows': _field_rows(PricingPlan, values, primary, labels=PLAN_LABELS),
            'details': _field_rows(PricingPlan, values, secondary, labels=PLAN_LABELS), 'translations': localized}


def _offers(tree, language, place):
    from catalog.models import Activity, OfferingGroup, Category, Subcategory, Program
    stored = Activity.objects.filter(place=place).in_bulk()
    categories = Category.objects.filter(pk__in=[a.get('category_id') for a in tree.get('activities', []) if a.get('category_id')]).in_bulk()
    subcategories = Subcategory.objects.filter(pk__in=[a.get('subcategory_id') for a in tree.get('activities', []) if a.get('subcategory_id')]).in_bulk()
    programs = Program.objects.filter(pk__in=[a.get('program_id') for a in tree.get('activities', []) if a.get('program_id')]).in_bulk()
    offers = []
    for activity in tree.get('activities', []):
        groups = []
        for group in activity.get('groups', []):
            groups.append({
                'title': group.get(f'name_{language}') or group.get('name_az') or group.get('name_ru') or group.get('name_en') or _('Группа'),
                'translations': _translations(group, [('name', _('Название группы')), ('conditions', _('Условия группы'))]),
                'rows': _field_rows(OfferingGroup, group, ('age_from','age_to','lesson_format','language','schedule_text','teachers_text'),
                    labels={'age_from':_('Возраст от'),'age_to':_('Возраст до'),'lesson_format':_('Формат занятий'),
                            'language':_('Язык занятий'),'schedule_text':_('Расписание группы'),'teachers_text':_('Преподаватели')}),
                'plans': [_plan(plan, language) for plan in group.get('pricing_plans', [])],
            })
        details = {'category':categories.get(activity.get('category_id')),
            'subcategory':subcategories.get(activity.get('subcategory_id')),
            'program':programs.get(activity.get('program_id'))}
        rows = _field_rows(Activity, details, ('category','subcategory','program'),
            labels={'category':_('Категория'),'subcategory':_('Подкатегория'),'program':_('Программа')})
        if activity.get('id') in stored:
            rows.append({'label':_('Статус'), 'value':stored[activity['id']].get_status_display()})
        offers.append({
            'title': activity.get(f'name_{language}') or activity.get('name_az') or activity.get('name_ru') or activity.get('name_en') or _('Направление'),
            'translations': _translations(activity, [('name', _('Название направления')), ('description', _('Описание направления')), ('supplement', _('Дополнение к программе'))]),
            'groups': groups, 'rows':rows,
        })
    return offers


def _review_summary(data, live, readiness, photos):
    """Describe the displayed snapshot; no moderation or publication decisions."""
    sections = {
        'gallery': (_('Галерея'), 'preview-photos'),
        'photo': (_('Главное фото'), 'preview-photos'),
        'cover_photo': (_('Фото для шапки'), 'preview-photos'),
        'structured_schedule': (_('Расписание по дням'), 'preview-schedule'),
        'pricing_plans': (_('Цены и тарифы'), 'preview-prices'),
        'nested_pricing': (_('Направления и группы'), 'preview-offers'),
        'location_override': (_('Адрес и контакты'), 'preview-location'),
    }
    changes = []
    for key in sorted(publication.fields_for('place')):
        current_value, displayed_value = live.get(key), data.get(key)
        if displayed_value == current_value:
            continue
        structured = isinstance(displayed_value, (dict, list)) or isinstance(current_value, (dict, list)) or key in {'photo','cover_photo','location_override'}
        if not structured:
            field = Place._meta.get_field(key)
            current_value = field.to_python(current_value) if current_value is not None else None
            displayed_value = field.to_python(displayed_value) if displayed_value is not None else None
        if displayed_value == current_value:
            continue
        if key in sections:
            label, target = sections[key]
        else:
            label = Place._meta.get_field(key).verbose_name
            target = ('preview-location' if key in {'address','district','metro','lat','lng','phone1','phone2','phone3','phone_country','whatsapp_mode','whatsapp_number','instagram','website'}
                else 'preview-schedule' if key.startswith('schedule')
                else 'preview-prices' if key.startswith(('price','custom_price'))
                else 'preview-conditions' if key.startswith(('extra_conditions','additional_info'))
                else 'preview-about')
        before = after = ''
        if not structured:
            before = _field_rows(Place, live, [key])[0]['value']
            after = _field_rows(Place, data, [key])[0]['value']
            if field.is_relation:
                related = field.remote_field.model.objects.in_bulk([value for value in (current_value, displayed_value) if value is not None])
                before = str(related.get(current_value) or _('Не указано'))
                after = str(related.get(displayed_value) or _('Не указано'))
        changes.append({'key':key, 'label':label, 'target':target, 'structured':structured,
            'before':before, 'after':after, 'removed':data.get(key) in (None, '')})
    languages = [{'language':lang, 'complete':all(str(data.get(f'{field}_{lang}') or '').strip()
        for field in ('name','description'))} for lang in LANGUAGES]
    activities = (data.get('nested_pricing') or {}).get('activities', [])
    available = sum(bool(photo['url']) for photo in photos)
    return {'changes':changes, 'change_count':len(changes),
        'ready_percent':round(100 * readiness.completed_count / readiness.required_count) if readiness.required_count else 0,
        'languages':languages, 'languages_complete':sum(row['complete'] for row in languages),
        'available_photos':available, 'missing_photos':len(photos)-available,
        'offer_count':len(activities), 'group_count':sum(len(a.get('groups', [])) for a in activities)}


def request_is_stale(item, *, revision=None):
    """Share the inspection freshness check with list and confirmation actions."""
    place = item.place
    is_publication = item.request_kind == item.KIND_PUBLICATION
    if revision is None and is_publication:
        revision = getattr(place, 'volunteer_revision', None)
    submitted = bool(is_publication and item.is_pending and revision and revision.status == 'pending')
    stale = bool(item.is_pending and (
        item.base_ownership_version != place.ownership_version or item.base_owner_id != place.owner_id
        or (is_publication and (item.base_content_version != place.content_version
            or item.base_candidate_version != (revision.version if revision else 0)
            or item.applicant_id != place.owner_id))))
    if submitted:
        from catalog.services.volunteer_places import revision_base_matches
        stale = stale or not revision.dependencies or not revision_base_matches(revision, place)
    return stale


def build_place_preview(place, *, language='ru'):
    """Inspect the saved working copy, falling back to the approved card."""
    revision = VolunteerPlaceRevision.objects.filter(
        place=place, status__in=('draft', 'pending', 'rejected')).first()
    preview = _build_preview(place, language=language, revision_candidate=revision)
    preview['saved_candidate'] = bool(revision)
    preview['saved_candidate_status'] = revision.status if revision else ''
    return preview


def build_request_preview(item, *, language='ru', current=False):
    return _build_preview(item.place, item=item, language=language, current=current)


def build_revision_preview(revision, *, language='ru', current=False):
    return _build_preview(revision.place, language=language,current=current,revision_candidate=revision)


def _build_preview(place, *, item=None, language='ru', current=False, revision_candidate=None):
    language = language if language in LANGUAGES else 'ru'
    live = publication.snapshot(place, 'place')
    revision = revision_candidate or VolunteerPlaceRevision.objects.filter(place=place).first()
    is_publication = bool(revision_candidate or (item and item.request_kind == item.KIND_PUBLICATION))
    submitted = bool((revision_candidate and revision.status != 'approved') or (is_publication and item and item.is_pending and revision and revision.status == 'pending'))
    data = copy.deepcopy(live)
    if submitted and not current:
        # A patch is not a full card. Preserve its complete captured base,
        # including unchanged group prices/photos and explicit empty values.
        data.update(copy.deepcopy(revision.base_snapshot or {}))
        data.update(copy.deepcopy(revision.payload))
    stale = request_is_stale(item, revision=revision) if item else False
    if revision_candidate and submitted:
        from catalog.services.volunteer_places import revision_base_matches
        stale = not revision_base_matches(revision,place)
    candidate = copy.copy(place)
    candidate._state = copy.copy(place._state)
    candidate._state.fields_cache = {}
    for name in publication.fields_for('place'):
        if name in {'pricing_plans','nested_pricing','structured_schedule','gallery','location_override'}:
            continue
        field = Place._meta.get_field(name)
        setattr(candidate, field.attname, field.to_python(data.get(name)))
    candidate.pricing_plans = data.get('pricing_plans', [])
    cleaned = {**data, 'category': candidate.category, 'subcategory': candidate.subcategory}
    readiness = evaluate_form_readiness(SimpleNamespace(cleaned_data=cleaned, instance=candidate,
        cleaned_schedule_days=data.get('structured_schedule', [])), candidate)
    photos = []
    for name, role in [('photo', _('Главное фото')), ('cover_photo', _('Фото для шапки'))]:
        if data.get(name): photos.append(_photo(data[name], '', role))
    for photo in data.get('gallery', []):
        photos.append(_photo(photo.get('image'), photo.get('caption', ''), _('Галерея'), gallery=True))
    # The publication snapshot contains legacy scalars as well as modern plans.
    legacy_names = ('price_from','price_to','price_per_lesson','price_per_month','price_per_8_lessons')
    basic = _field_rows(Place, data, ('nature','operating_state','age_from','age_to','age_open_ended','age_varies_by_program', 'offers_adult_classes',
        'lesson_format','lesson_duration_minutes','lessons_per_week','lessons_per_month'),
        labels={'nature':_('Тип карточки'),'operating_state':_('Состояние работы')})
    basic[:0] = [{'label': _('Категория'), 'value': str(candidate.category or _('Не указано'))},
                  {'label': _('Подкатегория'), 'value': str(candidate.subcategory or _('Не указано'))}]
    location = _field_rows(Place, {**data, 'city':place.city}, ('city','district','metro','address','lat','lng'))
    from catalog.services.locations import get_location_translation
    for index, name in enumerate(('city','district')):
        if name == 'city': location[index]['label'] = _('Город')
        if (place.city if name == 'city' else data.get(name)):
            location[index]['value'] = get_location_translation(place.city if name == 'city' else data[name], language)
    contacts = _field_rows(Place, data, ('phone1','phone2','phone3','phone_country','whatsapp_mode','whatsapp_number','instagram','website'))
    contacts.extend({'label':link['label'],'value':link['url'],'url':external_link(link['url'])} for link in candidate.safe_public_links)
    instagram = external_link(candidate.instagram_url()) if candidate.instagram else ''
    if instagram:
        next(row for row in contacts if row['label'] == Place._meta.get_field('instagram').verbose_name)['url'] = instagram
    organization = place.organization
    if organization:
        location.append({'label': _('Организация'), 'value': str(organization)})
        contacts.extend([{'label': _('Телефон организации'), 'value': organization.phone or _('Не указано')},
                         {'label': _('Сайт организации'), 'value': organization.website or _('Не указано'), 'url':external_link(organization.website)}])
    return {
        'title': data.get(f'name_{language}') or data.get('name_az') or data.get('name_ru') or data.get('name_en') or place.name,
        'place':place, 'is_publication':is_publication, 'has_submission':submitted,
        'candidate':candidate, 'snapshot':data,
        'submitted_fields':frozenset(revision.payload) if submitted and not current else frozenset(),
        'owner_label': (place.owner.get_full_name() or place.owner.username) if place.owner else _('Не указано'),
        'show_submission':submitted and not current, 'stale':stale,
        'readiness':readiness, 'basic':basic, 'location':location, 'contacts':contacts,
        'review':_review_summary(data, live, readiness, photos),
        'texts':_translations(data, [('name', _('Название')), ('description', _('Описание'))]),
        'conditions':_translations(data, [('extra_conditions', _('Дополнительные условия')), ('additional_info', _('Дополнительная информация'))]),
        'legacy_conditions':_field_rows(Place, data, ('extra_conditions','additional_info')),
        'photos':photos, 'photo_count':len(photos),
        'schedule_mode':dict(Place.SCHEDULE_MODE_CHOICES).get(data.get('schedule_mode'), data.get('schedule_mode')),
        'schedule_rows':build_schedule_rows(data.get('structured_schedule', []), language),
        'schedule_text':data.get('schedule',''),
        'schedule_notes':_translations(data, [('schedule_note', _('Примечание к расписанию'))]),
        'price_mode':dict(Place.PRICE_MODE_CHOICES).get(data.get('price_mode'), data.get('price_mode')),
        'price_badges':_translations(data, [('custom_price_badge', _('Надпись цены на карточке'))]),
        'plans':[_plan(plan, language) for plan in data.get('pricing_plans', [])],
        'legacy_prices':_field_rows(Place, data, legacy_names),
        'offers':_offers(data.get('nested_pricing') or {'activities':[]}, language, place),
    }
