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
    compact = getattr(form, 'compact_contact_fields', False)
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
        if compact:
            field.help_text = text('Номер Азербайджана: 050 123 45 67 или +994 50 123 45 67. Для другой страны укажите +код.', 'Azərbaycan nömrəsi: 050 123 45 67 və ya +994 50 123 45 67. Başqa ölkə üçün +kod daxil edin.', 'Azerbaijan number: 050 123 45 67 or +994 50 123 45 67. For another country include +code.')
        if 'phone_country' not in form.fields:
            field.help_text = text('Местные номера — Азербайджан (+994). Для другой страны укажите +код. Формат не подтверждает существование номера.', 'Yerli nömrələr üçün Azərbaycan (+994) istifadə olunur. Başqa ölkə üçün +kod daxil edin. Format nömrənin mövcudluğunu təsdiqləmir.', 'Local numbers default to Azerbaijan (+994). For another country include +code. Formatting does not confirm that a number exists.')
        if name in ('whatsapp_number', 'whatsapp'):
            field.help_text = text('Номер с кодом страны или ссылка https://wa.me/номер. Наличие аккаунта не проверяется.', 'Ölkə kodu ilə nömrə və ya https://wa.me/nömrə keçidi. Hesabın mövcudluğu yoxlanılmır.', 'Number with country code or https://wa.me/number. Account existence is not verified.')
            field.label = 'WhatsApp' if name == 'whatsapp' else text('Отдельный номер WhatsApp', 'Ayrıca WhatsApp nömrəsi', 'Separate WhatsApp number')
    if 'phone_country' in form.fields:
        original = form.initial.get('phone_country') or getattr(form.instance, 'phone_country', 'AZ') or 'AZ'
        form.fields['phone_country'] = forms.ChoiceField(required=True, label=text('Страна местного номера', 'Yerli nömrənin ölkəsi', 'Country for local numbers'), choices=[(r, f'{r} (+{phonenumbers.country_code_for_region(r)})') for r in sorted(phonenumbers.SUPPORTED_REGIONS)], widget=forms.Select(attrs={'class': 'field'}))
        form.initial['phone_country'] = original
        if compact:
            form.fields['phone_country'].widget = forms.HiddenInput(attrs={'data-km-local-default':'AZ'})
    if 'whatsapp_mode' in form.fields:
        instance = getattr(form, 'instance', None)
        original = (form.initial.get('whatsapp_mode') or getattr(instance, 'whatsapp_mode', 'legacy')) if getattr(instance, 'pk', None) else 'same'
        if compact and not getattr(instance, 'pk', None):
            original = 'none'
        choices = [('same', text('WhatsApp совпадает с телефоном', 'WhatsApp telefon nömrəsi ilə eynidir', 'WhatsApp uses the phone number')), ('separate', text('Отдельный номер WhatsApp', 'Ayrıca WhatsApp nömrəsi', 'Separate WhatsApp number')), ('none', text('WhatsApp отсутствует', 'WhatsApp yoxdur', 'No WhatsApp'))]
        if compact:
            choices[-1] = ('none', text('Не указывать WhatsApp', 'WhatsApp göstərilməsin', 'Do not show WhatsApp'))
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


def _contact_input_region(form, name, value, region):
    if getattr(form, 'compact_contact_fields', False) and (
            getattr(getattr(form, 'instance', None), 'pk', None) or form._preserve_existing_contacts):
        original = form._original_contact_values.get(name, '')
        original_region = form.initial.get('phone_country') or getattr(form.instance, 'phone_country', 'AZ') or 'AZ'
        if value in (original.strip(), format_phone(original, default_region=original_region).strip()):
            return original_region
    return region


def _contact_error(form, error):
    if getattr(form, 'compact_contact_fields', False) and getattr(error, 'code', None) == 'invalid_phone':
        return ValidationError(text(
            'Укажите корректный номер: 050 123 45 67 или +994 50 123 45 67. Для другой страны используйте международный +код.',
            'Düzgün nömrə daxil edin: 050 123 45 67 və ya +994 50 123 45 67. Başqa ölkə üçün beynəlxalq +kod istifadə edin.',
            'Enter a valid number: 050 123 45 67 or +994 50 123 45 67. For another country use the international +code.'),code='invalid_phone')
    return error


def clean_contact_form(form, cleaned):
    region = cleaned.get('phone_country') or 'AZ'
    for name, original in form._original_contact_values.items():
        if name not in cleaned:
            continue
        value = str(cleaned.get(name) or '').strip()
        input_region = _contact_input_region(form, name, value, region)
        try:
            normalizer = normalize_whatsapp if name in ('whatsapp_number', 'whatsapp') else normalize_phone
            cleaned[name] = normalizer(value, default_region=input_region)
        except ValidationError as exc:
            # Historical invalid numbers need manual review, not invented repairs.
            # An unrelated edit must still round-trip the untouched raw value.
            if (getattr(getattr(form, 'instance', None), 'pk', None) or form._preserve_existing_contacts) and value in (original.strip(), format_phone(original).strip()):
                cleaned[name] = original
            else:
                form.add_error(name, _contact_error(form, exc))
    if cleaned.get('whatsapp_mode') == 'separate' and not cleaned.get('whatsapp_number') and 'whatsapp_number' not in form.errors:
        form.add_error('whatsapp_number', text('Укажите отдельный номер WhatsApp.', 'Ayrıca WhatsApp nömrəsini daxil edin.', 'Enter the separate WhatsApp number.'))
    return cleaned


class ContactPhoneFormMixin:
    @property
    def editor_errors(self):
        if not self.is_bound:return {}
        # The publication summary repeats the same field issues. Keep genuine
        # non-field failures (for example a version conflict) visible.
        errors=self.errors.as_data();has_fields=any(name!='__all__' for name in errors)
        result={}
        for name,items in errors.items():
            messages=[str(message) for error in items
                if not (has_fields and name=='__all__' and error.code=='publication_incomplete')
                for message in error.messages]
            if messages:result[name]=messages
        return result

    @property
    def editor_error_targets(self):
        return {name:[(error.params or {}).get('field_path') for error in errors]
            for name,errors in self.errors.as_data().items()} if self.is_bound else {}

    def __init__(self, *args, **kwargs):
        self._preserve_existing_contacts = kwargs.pop('preserve_existing_contacts', False)
        super().__init__(*args, **kwargs)
        configure_contact_form(self)
        if 'instagram' in self.fields:
            self._original_instagram_value = self.initial.get(
                'instagram', getattr(getattr(self, 'instance', None), 'instagram', '')) or ''
            # Do not silently erase whitespace/control characters before validation.
            self.fields['instagram'].strip = False

    def clean_instagram(self):
        from catalog.services.place_social_profiles import validate_instagram_profile
        value = self.cleaned_data.get('instagram') or ''
        try:
            return validate_instagram_profile(value)
        except ValidationError:
            if (getattr(getattr(self, 'instance', None), 'pk', None) or self._preserve_existing_contacts) and value == self._original_instagram_value:
                return self._original_instagram_value
            raise

    def _clean_phone(self, name):
        value = str(self.cleaned_data.get(name) or '').strip()
        region = self.cleaned_data.get('phone_country') or self.data.get(self.add_prefix('phone_country')) or self.initial.get('phone_country') or 'AZ'
        region = _contact_input_region(self, name, value, region)
        try:
            return normalize_phone(value, default_region=region)
        except ValidationError as exc:
            original = self._original_contact_values.get(name, '')
            if (getattr(getattr(self, 'instance', None), 'pk', None) or self._preserve_existing_contacts) and value in (original.strip(), format_phone(original, default_region=region).strip()):
                return original
            error = _contact_error(self, exc)
            if error is exc:
                raise
            raise error from exc

    def clean_phone1(self):
        return self._clean_phone('phone1')

    def clean_phone2(self):
        return self._clean_phone('phone2')

    def clean_phone3(self):
        return self._clean_phone('phone3')

    def clean(self):
        return clean_contact_form(self, super().clean())
