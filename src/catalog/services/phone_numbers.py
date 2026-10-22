"""Canonical contact numbers. Validation establishes a pattern, not ownership."""
import re
from urllib.parse import urlsplit

import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import get_language


def contact_copy(ru, az, en):
    return {'ru': ru, 'az': az, 'en': en}.get((get_language() or 'az').split('-')[0], en)


def phone_error():
    return ValidationError(contact_copy(
        'Укажите корректный номер с кодом страны, например +994 50 427 43 93. Для местного номера выберите страну. Цифры не обрезаются.',
        'Ölkə kodu ilə düzgün nömrə daxil edin, məsələn +994 50 427 43 93. Yerli nömrə üçün ölkəni seçin. Rəqəmlər kəsilmir.',
        'Enter a valid number with its country code, for example +994 50 427 43 93. Select a country for a local number. Digits are never truncated.'), code='invalid_phone')


def normalize_phone(value, *, default_region='AZ', required=False):
    """Accept one formatted number; explicit +/00 overrides the selected region."""
    if value is None:
        value = ''
    if not isinstance(value, str):
        raise phone_error()
    raw = value.strip()
    if not raw:
        if required:
            raise ValidationError(contact_copy('Укажите номер телефона.', 'Telefon nömrəsini daxil edin.',
                                               'Enter the phone number.'), code='required')
        return ''
    region = str(default_region or 'AZ').upper()
    if region not in phonenumbers.SUPPORTED_REGIONS or len(raw) > 80:
        raise phone_error()
    raw = re.sub(r'\s+', ' ', raw)
    if raw.startswith('00'):
        raw = '+' + raw[2:].lstrip()
    if not re.fullmatch(r'\+?[0-9 ()-]+', raw):
        raise phone_error()
    try:
        number = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException as exc:
        raise phone_error() from exc
    canonical = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    if number.extension or not phonenumbers.is_valid_number(number) or not re.fullmatch(r'\+[1-9][0-9]{6,14}', canonical):
        raise phone_error()
    return canonical


def safe_phone(value, *, default_region='AZ'):
    """Return no callable link for unconfirmed legacy junk; never repair storage."""
    try:
        return normalize_phone(value, default_region=default_region)
    except ValidationError:
        return ''


def format_phone(value, *, default_region='AZ'):
    canonical = safe_phone(value, default_region=default_region)
    if not canonical:
        return value if isinstance(value, str) else ''
    return phonenumbers.format_number(phonenumbers.parse(canonical, None),
                                     phonenumbers.PhoneNumberFormat.INTERNATIONAL)


def normalize_whatsapp(value, *, default_region='AZ'):
    """Only a phone or canonical wa.me URL; arbitrary URLs are never followed."""
    if not isinstance(value, str):
        raise phone_error()
    raw = value.strip()
    if raw.startswith('https://'):
        try:
            parsed = urlsplit(raw)
        except ValueError as exc:
            raise phone_error() from exc
        if (parsed.scheme != 'https' or parsed.netloc != 'wa.me' or parsed.query or parsed.fragment
                or not re.fullmatch(r'/[1-9][0-9]{6,14}/?', parsed.path)):
            raise ValidationError(contact_copy(
                'Укажите номер WhatsApp или ссылку https://wa.me/номер без дополнительных параметров.',
                'WhatsApp nömrəsi və ya əlavə parametrsiz https://wa.me/nömrə keçidi daxil edin.',
                'Enter a WhatsApp number or an https://wa.me/number link without extra parameters.'), code='invalid_whatsapp')
        raw = '+' + parsed.path.strip('/')
    return normalize_phone(raw, default_region=default_region)


def normalize_contact_patch(target, patch, *, pending=None):
    """Validate contact intent at the publication boundary, including partial edits."""
    result = dict(patch)
    previous = dict(pending or {})
    def merged(name, default=''):
        return result.get(name, previous.get(name, getattr(target, name, default)))
    region = merged('phone_country', 'AZ')
    if region not in phonenumbers.SUPPORTED_REGIONS:
        raise phone_error()
    names = ('phone1', 'phone2', 'phone3', 'phone', 'whatsapp_number', 'whatsapp')
    for name in names:
        if name not in result:
            continue
        value = result[name]
        normalizer = normalize_whatsapp if name in {'whatsapp_number', 'whatsapp'} else normalize_phone
        try:
            result[name] = normalizer(value, default_region=region)
        except ValidationError:
            # Do not force historical junk through a lossy repair on unrelated edits.
            if not isinstance(value, str) or value != previous.get(name, getattr(target, name, '')):
                raise
    if ('whatsapp_mode' in result or 'whatsapp_number' in result) and merged('whatsapp_mode') == 'separate':
        if not normalize_whatsapp(merged('whatsapp_number'), default_region=region):
            raise phone_error()
    return result
