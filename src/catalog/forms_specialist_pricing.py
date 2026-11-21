"""Validate the required lesson offer and ordered optional package rows."""
from itertools import zip_longest

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import Specialist


PACKAGE_PERIODS = ('month', 'package')
PACKAGE_KEYS = ('period', 'amount', 'sessions')
PACKAGE_POST_FIELDS = tuple('package_' + key for key in PACKAGE_KEYS)
MAX_PACKAGES = 10


class LessonAmountField(forms.DecimalField):
    def __init__(self, **kwargs):
        super().__init__(min_value=0, max_digits=10, decimal_places=2, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace(',', '.')
        return super().to_python(value)


def submitted_package_rows(data):
    def column(key):
        if hasattr(data, 'getlist'):
            return data.getlist(key)
        value = data.get(key, [])
        return value if isinstance(value, (list, tuple)) else [value]

    columns = [column(key) for key in PACKAGE_POST_FIELDS]
    return [dict(zip(PACKAGE_KEYS, values)) for values in zip_longest(*columns, fillvalue='')
            if any(value not in ('', None) for value in values)]


def normalize_pricing_packages(rows):
    result = []
    money = LessonAmountField()
    sessions_field = forms.IntegerField(min_value=1, max_value=2_147_483_647)
    if not isinstance(rows, list):
        raise ValidationError(_('Проверьте дополнительные тарифы.'))
    if len(rows) > MAX_PACKAGES:
        raise ValidationError(_('Можно добавить не больше %(count)s тарифов.'), params={'count': MAX_PACKAGES})
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get('period') not in PACKAGE_PERIODS:
            raise ValidationError(_('Тариф %(row)s: выберите месяц или пакет занятий.'), params={'row': index})
        try:
            amount = money.clean(row.get('amount'))
            if amount is None or amount <= 0:
                # A free lesson is the base price set to 0; a package must cost something.
                raise ValidationError('')
        except ValidationError:
            raise ValidationError(_('Тариф %(row)s: укажите полную стоимость больше 0 ₼ (можно с гяпиками).'),
                                  params={'row': index}) from None
        try:
            sessions = sessions_field.clean(row.get('sessions'))
        except ValidationError:
            raise ValidationError(_('Тариф %(row)s: укажите целое число занятий от одного.'),
                                  params={'row': index}) from None
        result.append({'period': row['period'], 'amount': format(amount, '.2f'), 'sessions': sessions})
    return result


def _base_errors(lesson_type, lesson_price):
    errors = {}
    if lesson_type not in dict(Specialist.LESSON_TYPE_CHOICES):
        errors['lesson_type'] = _('Выберите тип занятия.')
    if lesson_price is None or lesson_price == '':
        errors['lesson_price'] = _('Укажите цену одного занятия.')
    return errors


def specialist_pricing_errors(lesson_type, lesson_price, packages):
    """Validate a saved profile before a staff moderation transition."""
    errors = _base_errors(lesson_type, lesson_price)
    try:
        normalize_pricing_packages(packages)
    except ValidationError as exc:
        errors['pricing_packages'] = exc.messages[0]
    return errors


class PackageRowsInput(forms.HiddenInput):
    def value_from_datadict(self, data, files, name):
        return submitted_package_rows(data)

    def value_omitted_from_data(self, data, files, name):
        # Submitting zero rows explicitly removes all of a profile's packages.
        return False


class SpecialistPricingFormMixin(forms.Form):
    lesson_price = LessonAmountField(required=False, label=_('Цена одного занятия (AZN)'),
                                    widget=forms.NumberInput(attrs={'class': 'field', 'inputmode': 'decimal', 'placeholder': '30',
                                                                  'min': '0', 'max': '99999999.99', 'step': '0.01'}))
    pricing_packages = forms.Field(required=False, widget=PackageRowsInput,
                                   label=_('Дополнительные тарифы'))

    @property
    def pricing_package_rows(self):
        if self.is_bound:
            return submitted_package_rows(self.data)
        return self.initial.get('pricing_packages') or []

    def clean_specialist_pricing(self, data, *, require):
        if require:
            for name, message in _base_errors(data.get('lesson_type'), data.get('lesson_price')).items():
                if name in self.fields and name not in self.errors:
                    self.add_error(name, message)
        if 'pricing_packages' in self.fields:
            rows = self.pricing_package_rows
            try:
                data['pricing_packages'] = normalize_pricing_packages(rows)
            except ValidationError as exc:
                if require:
                    self.add_error('pricing_packages', exc)
                else:
                    data['pricing_packages'] = rows
