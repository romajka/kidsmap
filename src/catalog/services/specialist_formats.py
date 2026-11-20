"""Specialist session formats, including read compatibility for older profiles."""
from django import forms
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import get_language

from catalog.models import District, SpecialistPracticeLocation

FORMAT_CODES = ('online', 'office', 'visit')
_FLAGS = dict(zip(FORMAT_CODES, ('offers_online', 'offers_office', 'offers_visits')))
_TEXT = {
    'online': ('Онлайн', 'Onlayn', 'Online'),
    'unspecified': ('Формат уточняется', 'Format dəqiqləşdirilir', 'Format to be confirmed'),
    'office': ('У специалиста', 'Mütəxəssisin qəbul yerində', 'At the specialist’s location'),
    'visit': ('Выезд к семье', 'Ailənin ünvanında', 'Home visits'),
    'legacy': ('Очно, место уточняется', 'Əyani, məkan dəqiqləşdirilir', 'In person, location to be confirmed'),
    'formats': ('Форматы занятий', 'Məşğələ formatları', 'Session formats'),
    'region': ('Город выезда', 'Səfər edilən şəhər', 'Home visit city'),
    'citywide': ('Весь город', 'Bütün şəhər', 'Entire city'),
    'districts': ('Районы выезда', 'Səfər edilən rayonlar', 'Home visit districts'),
    'empty': ('Выберите хотя бы один формат.', 'Ən azı bir format seçin.', 'Select at least one format.'),
    'missing_region': ('Выберите город для выезда.', 'Səfər üçün şəhər seçin.', 'Choose a city for home visits.'),
    'missing_area': ('Отметьте «Весь город» или выберите районы выезда.',
                     '“Bütün şəhər” seçin və ya səfər edilən rayonları qeyd edin.',
                     'Select the entire city or choose home visit districts.'),
    'wrong_region': ('Выберите районы из указанного города.', 'Seçilmiş şəhərin rayonlarını qeyd edin.',
                     'Choose districts within the selected city.'),
    'missing_office': ('Для приёма у специалиста укажите город и действующий центр или адрес.',
                       'Mütəxəssisin qəbul yerində qəbul üçün şəhər və fəaliyyət göstərən mərkəz və ya ünvan seçin.',
                       'For sessions at the specialist’s location, specify a city and an active centre or address.'),
}


def _text(key, language=None):
    lang = (language or get_language() or 'az').split('-')[0]
    return _TEXT[key][{'ru': 0, 'az': 1, 'en': 2}.get(lang, 1)]


def format_choices(language=None):
    return [(code, _text(code, language)) for code in FORMAT_CODES]


def legacy_format_codes(value):
    return {'online': ('online',), 'offline': ('office',), 'in_person': ('office',), 'both': ('online', 'office')}.get(value, ())


def office_requested(person):
    return person.offers_office or 'office' in legacy_format_codes(person.consultation_format)


def _valid_offices():
    return SpecialistPracticeLocation.objects.filter(is_active=True, region__isnull=False).filter(
        Q(place__isnull=False) | ~Q(address__regex=r'^\s*$')
    )


def has_office(person):
    if not person.pk:
        return False
    cached = getattr(person, '_prefetched_objects_cache', {}).get('practice_locations')
    if cached is not None:
        return any(loc.is_active and loc.region_id and (loc.place_id or loc.address.strip()) for loc in cached)
    return _valid_offices().filter(specialist_id=person.pk).exists()


def profile_format_codes(person):
    legacy = legacy_format_codes(person.consultation_format)
    codes = {code for code, field in _FLAGS.items() if getattr(person, field)}
    if 'online' in legacy:
        codes.add('online')
    if 'office' in legacy and 'office' not in codes and has_office(person):
        codes.add('office')
    return tuple(code for code in FORMAT_CODES if code in codes)


def format_labels(person, language=None):
    codes = profile_format_codes(person)
    labels = [_text(code, language) for code in codes]
    if 'office' in legacy_format_codes(person.consultation_format) and 'office' not in codes:
        labels.append(_text('legacy', language))
    return labels or [_text('unspecified', language)]


def public_format_label(person, language=None):
    return ' · '.join(format_labels(person, language))


def format_q(code, prefix=''):
    if code == 'online':
        return Q(**{prefix+'offers_online': True}) | Q(**{prefix+'consultation_format__in': ('online', 'both')})
    if code == 'visit':
        return Q(**{prefix+'offers_visits': True})
    old_office = Q(**{prefix+'consultation_format__in': ('offline', 'in_person', 'both')})
    if code == 'offline':
        return Q(**{prefix+'offers_office': True}) | Q(**{prefix+'offers_visits': True}) | old_office
    if code == 'office':
        valid = _valid_offices().filter(specialist_id=OuterRef(prefix+'pk'))
        return Q(**{prefix+'offers_office': True}) | (old_office & Q(Exists(valid)))
    return Q(**{prefix+'pk__in': []})


def apply_formats_to_instance(instance, codes):
    for code, field in _FLAGS.items():
        setattr(instance, field, code in codes)
    # Old readers can still interpret office and online. Visits alone have no legacy equivalent.
    instance.consultation_format = (
        'both' if instance.offers_online and instance.offers_office
        else 'online' if instance.offers_online else 'offline' if instance.offers_office else ''
    )


def validate_visit_area(codes, region, citywide, districts, *, allow_incomplete=False):
    if 'visit' not in codes:
        return {}
    errors = {}
    if not region and not allow_incomplete:
        errors['visit_region'] = _text('missing_region')
    if not citywide:
        districts = list(districts)
        if not districts and not allow_incomplete:
            errors['visit_districts'] = _text('missing_area')
        elif region and any(district.region_id != region.pk for district in districts):
            errors['visit_districts'] = _text('wrong_region')
    return errors


def missing_office_message():
    return _text('missing_office')


def profile_format_errors(person):
    codes = profile_format_codes(person)
    errors = []
    if not codes and 'office' not in legacy_format_codes(person.consultation_format):
        errors.append(_text('empty'))
    if office_requested(person) and not has_office(person):
        errors.append(_text('missing_office'))
    if 'visit' in codes:
        errors.extend(validate_visit_area(codes, person.visit_region, person.visit_citywide,
                                          person.visit_districts.all()).values())
    return errors


class DistrictCheckboxes(forms.CheckboxSelectMultiple):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if getattr(value, 'instance', None):
            option['attrs']['data-region'] = value.instance.region_id
        return option


class SpecialistFormatsFormMixin(forms.Form):
    session_formats = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)

    def _init_format_fields(self):
        self.fields['session_formats'].choices = format_choices()
        self.fields['session_formats'].label = _text('formats')
        if 'session_formats' not in self.initial:
            self.initial['session_formats'] = profile_format_codes(self.instance) if self.instance.pk else ()
        if self.is_bound:
            data = self.data.copy()
            codes = (data.getlist('session_formats') if hasattr(data, 'getlist') else data.get('session_formats', []))
            if 'session_formats' not in data and data.get('consultation_format'):
                codes = legacy_format_codes(data['consultation_format'])
                if hasattr(data, 'setlist'):
                    data.setlist('session_formats', list(codes))
                else:
                    data['session_formats'] = list(codes)
            if 'session_formats' in data:
                # The scalar can be present in an older open tab or returned draft.
                # Prevent it from overriding or invalidating an explicit current selection.
                data.pop('consultation_format', None)
            if 'visit' not in codes:
                for key in ('visit_region', 'visit_citywide', 'visit_districts'):
                    data.pop(key, None)
            elif forms.CheckboxInput().value_from_datadict(data, {}, 'visit_citywide'):
                data.pop('visit_districts', None)
            self.data = data
        if 'visit_region' in self.fields:
            region = self.fields['visit_region']
            region.label = _text('region')
            region.label_from_instance = lambda city: city.name_i18n()
            region.widget = forms.Select(attrs={'class': 'field'})
            region.widget.choices = region.choices
        if 'visit_citywide' in self.fields:
            self.fields['visit_citywide'].label = _text('citywide')
        if 'visit_districts' in self.fields:
            districts = self.fields['visit_districts']
            districts.label = _text('districts')
            districts.widget = DistrictCheckboxes()
            districts.label_from_instance = lambda district: district.name_i18n()
            districts.queryset = District.objects.all()

    def clean_format_fields(self, cleaned, *, require, allow_incomplete):
        codes = cleaned.get('session_formats') or ()
        if require and not codes and 'session_formats' not in self.errors:
            self.add_error('session_formats', _text('empty'))
        for field, message in validate_visit_area(
            codes, cleaned.get('visit_region'), cleaned.get('visit_citywide'),
            cleaned.get('visit_districts') or (), allow_incomplete=allow_incomplete,
        ).items():
            if field not in self.errors:
                self.add_error(field, message)
        apply_formats_to_instance(self.instance, codes)
        if 'consultation_format' in self.fields:
            cleaned['consultation_format'] = self.instance.consultation_format
        return cleaned
