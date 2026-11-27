"""Typed Event price and explicit registration, with conservative legacy reads."""
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from catalog.services.phone_numbers import contact_copy, normalize_phone, normalize_whatsapp


EVENT_UI_CONFIG = {
    'priceFields': {'legacy': ['price_text'], 'free': [], 'fixed': ['price_amount', 'price_currency'],
        'from': ['price_amount', 'price_currency'], 'range': ['price_amount', 'price_amount_max', 'price_currency'], 'unknown': []},
    'registrationFields': {'phone': ['phone'], 'whatsapp': ['whatsapp'], 'link': ['registration_url']},
}
# Exact labels only: "free entry, workshop 15 AZN" must never become free.
_FREE_TOKEN = r'(?:pulsuz|ödənişsiz|бесплатно|free|0(?:[.,]0{1,2})?(?:\s*azn)?)'
LEGACY_FREE_PATTERN = rf'^\s*{_FREE_TOKEN}(?:\s*[/|]\s*{_FREE_TOKEN})*\s*$'


def legacy_is_free(value):
    return bool(re.fullmatch(LEGACY_FREE_PATTERN, str(value or ''), re.IGNORECASE))


def is_free(event):
    return event.price_mode == 'free' or (event.price_mode == 'legacy' and legacy_is_free(event.price_text))


def _amount(value):
    return format(Decimal(value), 'f').rstrip('0').rstrip('.') if Decimal(value) % 1 else str(int(Decimal(value)))


def price_display(event):
    mode = event.price_mode
    if is_free(event):
        return contact_copy('Бесплатно', 'Ödənişsiz', 'Free')
    if mode == 'unknown':
        return contact_copy('Уточнить стоимость', 'Qiyməti dəqiqləşdirin', 'Ask for price')
    if mode in {'fixed', 'from', 'range'} and event.price_amount is not None:
        amount = _amount(event.price_amount)
        if mode == 'range' and event.price_amount_max is not None:
            amount += '–' + _amount(event.price_amount_max)
        value = f'{amount} {event.price_currency}'
        if mode == 'from':
            return contact_copy('от '+value, value+'-dan', 'from '+value)
        return value
    return str(event.price_text or '').strip()


def _registration_url(event):
    method = event.registration_method
    try:
        if method == 'phone':
            number = normalize_phone(event.phone)
            return 'tel:'+number if number else ''
        if method == 'whatsapp':
            number = normalize_whatsapp(event.whatsapp)
            return 'https://wa.me/'+number.lstrip('+') if number else ''
        if method == 'link':
            value = str(event.registration_url or '').strip()
            URLValidator(schemes=['http', 'https'])(value)
            parsed = urlsplit(value)
            if parsed.username or parsed.password:
                return ''
            return value
    except (ValidationError, ValueError):
        pass
    return ''


def registration(event):
    method = event.registration_method
    labels = {'phone': contact_copy('Позвонить', 'Zəng etmək', 'Call'),
        'whatsapp': contact_copy('Записаться в WhatsApp', 'WhatsApp ilə yazılmaq', 'Register via WhatsApp'),
        'link': contact_copy('Записаться', 'Qeydiyyatdan keçmək', 'Register')}
    return {'url': _registration_url(event), 'label': labels.get(method, ''), 'kind': method}


def detail_errors(event, original=None):
    """Validate supplied data even for drafts, without requiring unfinished fields."""
    errors = {}
    mode = event.price_mode
    if mode not in EVENT_UI_CONFIG['priceFields']:
        errors['price_mode'] = contact_copy('Выберите тип цены.', 'Qiymət növünü seçin.', 'Choose a price type.')
    if event.price_currency not in {'AZN', 'USD', 'EUR'}:
        errors['price_currency'] = contact_copy('Выберите валюту.', 'Valyutanı seçin.', 'Choose a currency.')
    amounts = {}
    for field in ('price_amount', 'price_amount_max'):
        value = getattr(event, field)
        if value is not None:
            try:
                number = Decimal(str(value))
                if not number.is_finite() or number < 0 or number >= Decimal('100000000') or number.as_tuple().exponent < -2:
                    raise InvalidOperation
                amounts[field] = number
            except (InvalidOperation, ValueError, TypeError):
                errors[field] = contact_copy('Укажите корректную цену.', 'Düzgün qiymət daxil edin.', 'Enter a valid price.')
    if mode in {'fixed', 'from', 'range'} and event.price_amount is None:
        errors['price_amount'] = contact_copy('Укажите цену.', 'Qiyməti daxil edin.', 'Enter the price.')
    if mode == 'range':
        if event.price_amount_max is None:
            errors['price_amount_max'] = contact_copy('Укажите верхнюю цену.', 'Yuxarı qiyməti daxil edin.', 'Enter the upper price.')
        elif 'price_amount' in amounts and 'price_amount_max' in amounts and amounts['price_amount_max'] < amounts['price_amount']:
            errors['price_amount_max'] = contact_copy('Верхняя цена меньше нижней.', 'Yuxarı qiymət aşağı qiymətdən kiçikdir.', 'The upper price is below the lower price.')
    if event.registration_method not in EVENT_UI_CONFIG['registrationFields']:
        errors['registration_method'] = contact_copy('Выберите способ записи.', 'Qeydiyyat üsulunu seçin.', 'Choose a registration method.')
    for field, normalizer in (('phone', normalize_phone), ('whatsapp', normalize_whatsapp)):
        # Old phone text may be retained on an unrelated edit. A fresh
        # submission/publication calls this without original and validates it.
        if field == 'phone' and original is not None and event.phone == original.phone:
            continue
        if getattr(event, field):
            try:
                normalizer(getattr(event, field))
            except ValidationError as exc:
                errors[field] = exc.messages[0]
    if event.registration_url and not _registration_url(type('Link', (), {'registration_method':'link', 'registration_url':event.registration_url})()):
        errors['registration_url'] = contact_copy('Укажите ссылку http:// или https:// без пароля.', 'Parolsuz http:// və ya https:// keçidi daxil edin.', 'Enter an http:// or https:// URL without credentials.')
    if event.age_from is not None and event.age_to is not None and event.age_from > event.age_to:
        errors['age_to'] = contact_copy('Возраст «до» меньше «от».', 'Yuxarı yaş aşağı yaşdan kiçikdir.', 'The upper age is below the lower age.')
    return errors
