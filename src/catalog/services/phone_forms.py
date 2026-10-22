"""Shared contact editing; model and publication validation use phone_numbers too."""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import get_language
import phonenumbers

from catalog.services.phone_numbers import format_phone, normalize_phone, normalize_whatsapp


def text(ru, az, en):
    return {'az': az, 'en': en}.get((get_language() or 'ru').split('-')[0], ru)


def configure_contact_form(form):
    form._original_contact_values = {}
    region = form.initial.get('phone_country') or getattr(getattr(form, 'instance', None), 'phone_country', 'AZ') or 'AZ'
    for name in ('phone1', 'phone2', 'phone3', 'phone', 'whatsapp_number', 'whatsapp'):
        if name not in form.fields:
            continue
        field = form.fields[name]
        original = form.initial.get(name, getattr(getattr(form, 'instance', None), name, '')) or ''
        form._original_contact_values[name] = str(original)
        field.required = False
        field.max_length = 80
        field.validators = [v for v in field.validators if not isinstance(v, MaxLengthValidator)] + [MaxLengthValidator(80)]
        field.widget.attrs.update({'autocomplete': 'tel', 'inputmode': 'tel', 'maxlength': '80', 'placeholder': '+994 50 123 45 67', 'data-km-phone': '1'})
        field.widget.attrs.pop('data-km-az-phone', None)
        form.initial[name] = format_phone(original, default_region=region)
        field.help_text = text('Местный номер — по выбранной стране. Для другой страны укажите +код. Формат не подтверждает существование номера.', 'Yerli nömrə seçilmiş ölkəyə görə yoxlanılır. Başqa ölkə üçün +kod daxil edin. Format nömrənin mövcudluğunu təsdiqləmir.', 'Local numbers use the selected country. For another country include +code. Formatting does not confirm that a number exists.')
        if 'phone_country' not in form.fields:
            field.help_text = text('Местные номера — Азербайджан (+994). Для другой страны укажите +код. Формат не подтверждает существование номера.', 'Yerli nömrələr üçün Azərbaycan (+994) istifadə olunur. Başqa ölkə üçün +kod daxil edin. Format nömrənin mövcudluğunu təsdiqləmir.', 'Local numbers default to Azerbaijan (+994). For another country include +code. Formatting does not confirm that a number exists.')
        if name in ('whatsapp_number', 'whatsapp'):
            field.help_text = text('Номер с кодом страны или ссылка https://wa.me/номер. Наличие аккаунта не проверяется.', 'Ölkə kodu ilə nömrə və ya https://wa.me/nömrə keçidi. Hesabın mövcudluğu yoxlanılmır.', 'Number with country code or https://wa.me/number. Account existence is not verified.')
            field.label = 'WhatsApp' if name == 'whatsapp' else text('Отдельный номер WhatsApp', 'Ayrıca WhatsApp nömrəsi', 'Separate WhatsApp number')
    if 'phone_country' in form.fields:
        original = form.initial.get('phone_country') or getattr(form.instance, 'phone_country', 'AZ') or 'AZ'
        form.fields['phone_country'] = forms.ChoiceField(required=True, label=text('Страна местного номера', 'Yerli nömrənin ölkəsi', 'Country for local numbers'), choices=[(r, f'{r} (+{phonenumbers.country_code_for_region(r)})') for r in sorted(phonenumbers.SUPPORTED_REGIONS)], widget=forms.Select(attrs={'class': 'field'}))
        form.initial['phone_country'] = original
    if 'whatsapp_mode' in form.fields:
        instance = getattr(form, 'instance', None)
        original = (form.initial.get('whatsapp_mode') or getattr(instance, 'whatsapp_mode', 'legacy')) if getattr(instance, 'pk', None) else 'same'
        choices = [('same', text('WhatsApp совпадает с телефоном', 'WhatsApp telefon nömrəsi ilə eynidir', 'WhatsApp uses the phone number')), ('separate', text('Отдельный номер WhatsApp', 'Ayrıca WhatsApp nömrəsi', 'Separate WhatsApp number')), ('none', text('WhatsApp отсутствует', 'WhatsApp yoxdur', 'No WhatsApp'))]
        if original == 'legacy':
            choices.insert(0, ('legacy', text('Как в существующей карточке', 'Mövcud kartdakı kimi', 'Keep existing behavior')))
        form.fields['whatsapp_mode'] = forms.ChoiceField(choices=choices, label='WhatsApp', widget=forms.Select(attrs={'class': 'field'}))
        form.initial['whatsapp_mode'] = original
    if form.is_bound:
        # Old clients and partial candidate saves must not clear newly added fields.
        data = form.data.copy()
        for name in ('phone_country', 'whatsapp_mode', 'whatsapp_number'):
            if name in form.fields and form.add_prefix(name) not in data:
                data[form.add_prefix(name)] = form.initial.get(name, '')
        form.data = data


def clean_contact_form(form, cleaned):
    region = cleaned.get('phone_country') or 'AZ'
    for name, original in form._original_contact_values.items():
        if name not in cleaned:
            continue
        value = str(cleaned.get(name) or '').strip()
        try:
            normalizer = normalize_whatsapp if name in ('whatsapp_number', 'whatsapp') else normalize_phone
            cleaned[name] = normalizer(value, default_region=region)
        except ValidationError as exc:
            # Historical invalid numbers need manual review, not invented repairs.
            # An unrelated edit must still round-trip the untouched raw value.
            if (getattr(getattr(form, 'instance', None), 'pk', None) or form._preserve_existing_contacts) and value in (original.strip(), format_phone(original).strip()):
                cleaned[name] = original
            else:
                form.add_error(name, exc)
    if cleaned.get('whatsapp_mode') == 'separate' and not cleaned.get('whatsapp_number') and 'whatsapp_number' not in form.errors:
        form.add_error('whatsapp_number', text('Укажите отдельный номер WhatsApp.', 'Ayrıca WhatsApp nömrəsini daxil edin.', 'Enter the separate WhatsApp number.'))
    return cleaned


class ContactPhoneFormMixin:
    def __init__(self, *args, **kwargs):
        self._preserve_existing_contacts = kwargs.pop('preserve_existing_contacts', False)
        super().__init__(*args, **kwargs)
        configure_contact_form(self)

    def _clean_phone(self, name):
        value = str(self.cleaned_data.get(name) or '').strip()
        region = self.cleaned_data.get('phone_country') or self.data.get(self.add_prefix('phone_country')) or self.initial.get('phone_country') or 'AZ'
        try:
            return normalize_phone(value, default_region=region)
        except ValidationError:
            original = self._original_contact_values.get(name, '')
            if (getattr(getattr(self, 'instance', None), 'pk', None) or self._preserve_existing_contacts) and value in (original.strip(), format_phone(original, default_region=region).strip()):
                return original
            raise

    def clean_phone1(self):
        return self._clean_phone('phone1')

    def clean_phone2(self):
        return self._clean_phone('phone2')

    def clean_phone3(self):
        return self._clean_phone('phone3')

    def clean(self):
        return clean_contact_form(self, super().clean())
