from __future__ import annotations

import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from catalog.content_data import BAKU_METRO_STATIONS
from catalog.models import CatalogContentSettings, Place, UserProfile
from catalog.services.options import sort_translated_values


User = get_user_model()
_NAME_CONNECTORS = {" ", "-", "'"}
_PHONE_RE = re.compile(r"^\+?[0-9()\-\s]{7,25}$")
_OWNER_IMAGE_MAX_BYTES = 2 * 1024 * 1024
_OWNER_GALLERY_MAX_FILES = 10


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _validate_person_name(value: str, *, field_label: str) -> str:
    normalized = _normalize_whitespace(value)
    if not normalized:
        raise ValidationError(_("%(field)s обязательно для заполнения.") % {"field": field_label})
    if len(normalized) < 2:
        raise ValidationError(_("%(field)s слишком короткое. Укажите минимум 2 символа.") % {"field": field_label})
    if normalized[0] in _NAME_CONNECTORS or normalized[-1] in _NAME_CONNECTORS:
        raise ValidationError(_("%(field)s содержит недопустимые символы.") % {"field": field_label})
    for char in normalized:
        if char in _NAME_CONNECTORS or char.isalpha():
            continue
        raise ValidationError(
            _("%(field)s должно содержать только буквы, пробел, дефис или апостроф.")
            % {"field": field_label}
        )
    return normalized


def _validate_phone(value: str) -> str:
    normalized = _normalize_whitespace(value)
    if not normalized:
        raise ValidationError(_("Укажите номер телефона."))
    if not _PHONE_RE.fullmatch(normalized):
        raise ValidationError(_("Введите корректный номер телефона. Пример: +994 50 123 45 67"))
    digits = "".join(char for char in normalized if char.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        raise ValidationError(_("Номер телефона должен содержать от 7 до 15 цифр."))
    return normalized


def _validate_uploaded_image(file_obj, *, max_bytes: int = _OWNER_IMAGE_MAX_BYTES) -> None:
    if not file_obj:
        return
    content_type = (getattr(file_obj, "content_type", "") or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise ValidationError(_("Загружайте только изображения (JPG, PNG, WEBP и т.д.)."))
    if getattr(file_obj, "size", 0) > max_bytes:
        raise ValidationError(_("Размер изображения не должен превышать 2 МБ."))


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    template_name = "widgets/multiple_file_input.html"


class ImagePreviewFileInput(forms.ClearableFileInput):
    template_name = "widgets/image_preview_file_input.html"


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            MultipleFileInput(
                attrs={
                    "class": "field owner-file-uploader-input",
                    "accept": "image/*",
                    "multiple": True,
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []

        if isinstance(data, (list, tuple)):
            items = data
        else:
            items = [data]

        cleaned_items = []
        single_clean = super().clean
        for item in items:
            if not item:
                continue
            cleaned_items.append(single_clean(item, initial))
        return cleaned_items


class RegistrationForm(UserCreationForm):
    error_messages = {
        "password_mismatch": _("Пароли не совпадают. Введите одинаковый пароль в обоих полях."),
    }
    first_name = forms.CharField(
        label=_("Имя"),
        required=True,
        max_length=150,
        error_messages={"required": _("Укажите имя.")},
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label=_("Фамилия"),
        required=True,
        max_length=150,
        error_messages={"required": _("Укажите фамилию.")},
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        error_messages={
            "required": _("Укажите email."),
            "invalid": _("Укажите корректный email."),
        },
        widget=forms.EmailInput(attrs={"class": "field", "autocomplete": "email"}),
    )
    phone = forms.CharField(
        label=_("Телефон"),
        required=True,
        max_length=32,
        error_messages={"required": _("Укажите номер телефона.")},
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "tel"}),
    )
    gender = forms.ChoiceField(
        label=_("Пол"),
        choices=UserProfile.REGISTRATION_GENDER_CHOICES,
        required=True,
        error_messages={
            "required": _("Выберите пол."),
            "invalid_choice": _("Выберите корректный вариант пола."),
        },
        widget=forms.RadioSelect(attrs={"class": "auth-role-option"}),
    )
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "field", "autocomplete": "username"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Логин")
        self.fields["username"].help_text = _("Только буквы, цифры и символы @/./+/-/_")
        self.fields["username"].error_messages.update(
            {
                "required": _("Укажите логин. Пример: ramin_01."),
                "invalid": _("Логин содержит недопустимые символы. Используйте буквы, цифры и @/./+/-/_."),
                "max_length": _("Логин слишком длинный. Используйте не более 150 символов."),
            }
        )
        self.fields["first_name"].help_text = _("Введите ваше настоящее имя.")
        self.fields["last_name"].help_text = _("Введите вашу настоящую фамилию.")
        self.fields["email"].help_text = _(
            "Укажите рабочий email: после регистрации на него придет код подтверждения."
        )
        self.fields["phone"].help_text = _("Номер нужен для связи по вашему аккаунту.")
        self.fields["gender"].help_text = _("Укажите ваш пол.")
        self.fields["password1"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})
        self.fields["password1"].label = _("Пароль")
        self.fields["password2"].label = _("Повторите пароль")
        self.fields["password1"].error_messages.update(
            {"required": _("Придумайте пароль, чтобы продолжить регистрацию.")}
        )
        self.fields["password2"].error_messages.update(
            {"required": _("Повторите пароль, чтобы подтвердить ввод.")}
        )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise ValidationError(_("Укажите логин. Пример: ramin_01."))
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_("Этот логин уже занят. Выберите другой, например добавьте цифры."))
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError(_("Укажите email."))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("Пользователь с таким email уже зарегистрирован. Войдите в аккаунт или используйте другой email.")
            )
        return email

    def clean_first_name(self):
        return _validate_person_name(self.cleaned_data.get("first_name") or "", field_label=str(_("Имя")))

    def clean_last_name(self):
        return _validate_person_name(self.cleaned_data.get("last_name") or "", field_label=str(_("Фамилия")))

    def clean_phone(self):
        return _validate_phone(self.cleaned_data.get("phone") or "")

    def clean_gender(self):
        gender = (self.cleaned_data.get("gender") or "").strip().upper()
        valid_values = {value for value, _ in UserProfile.REGISTRATION_GENDER_CHOICES}
        if gender not in valid_values:
            raise ValidationError(_("Выберите корректный вариант пола."))
        return gender

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _(
            "Не удалось войти. Проверьте логин и пароль (раскладку, Caps Lock) и попробуйте снова."
        ),
        "inactive": _("Этот аккаунт временно отключен. Обратитесь к администратору."),
    }
    username = forms.CharField(
        label=_("Логин или email"),
        error_messages={
            "required": _("Укажите логин или email."),
        },
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "username"}),
    )
    password = forms.CharField(
        label=_("Пароль"),
        strip=False,
        error_messages={
            "required": _("Укажите пароль."),
        },
        widget=forms.PasswordInput(attrs={"class": "field", "autocomplete": "current-password"}),
    )
    remember_me = forms.BooleanField(
        label=_("Запомнить меня"),
        required=False,
        initial=False,
    )

    def clean(self):
        login_value = (self.cleaned_data.get("username") or "").strip()
        password = self.cleaned_data.get("password") or ""
        if not login_value or not password:
            return self.cleaned_data

        user = (
            User.objects.filter(Q(username__iexact=login_value) | Q(email__iexact=login_value))
            .order_by("id")
            .first()
        )
        resolved_username = user.username if user else login_value
        self.cleaned_data["username"] = resolved_username

        if user and not user.is_active and user.check_password(password):
            raise ValidationError(
                _("Email не подтвержден. Подтвердите email кодом из письма, затем повторите вход."),
                code="email_not_verified",
            )

        self.user_cache = authenticate(self.request, username=resolved_username, password=password)
        if self.user_cache is None:
            raise self.get_invalid_login_error()

        try:
            self.confirm_login_allowed(self.user_cache)
        except ValidationError as exc:
            if user and not user.is_active and user.check_password(password):
                raise ValidationError(
                    _("Email не подтвержден. Подтвердите email кодом из письма, затем повторите вход."),
                    code="email_not_verified",
                )
            raise exc

        return self.cleaned_data


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "field", "autocomplete": "email"}),
        error_messages={
            "required": _("Укажите email."),
            "invalid": _("Укажите корректный email."),
        },
    )
    code = forms.CharField(
        label=_("Код подтверждения"),
        required=True,
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "field",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": r"\d{6}",
                "placeholder": "123456",
            }
        ),
        error_messages={
            "required": _("Введите код подтверждения."),
            "min_length": _("Код должен содержать 6 цифр."),
            "max_length": _("Код должен содержать 6 цифр."),
        },
    )

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code.isdigit():
            raise ValidationError(_("Код должен состоять только из цифр."))
        return code


class EmailVerificationResendForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "field", "autocomplete": "email"}),
        error_messages={
            "required": _("Укажите email."),
            "invalid": _("Укажите корректный email."),
        },
    )

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()


class UserProfileEditForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        error_messages={
            "required": _("Укажите email."),
            "invalid": _("Укажите корректный email."),
        },
        widget=forms.EmailInput(attrs={"class": "field", "autocomplete": "email"}),
    )
    first_name = forms.CharField(
        label=_("Имя"),
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label=_("Фамилия"),
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "family-name"}),
    )
    phone = forms.CharField(
        label=_("Телефон"),
        required=True,
        max_length=32,
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "tel"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError(_("Укажите email."))
        qs = User.objects.filter(email__iexact=email)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError(_("Пользователь с таким email уже зарегистрирован. Укажите другой email."))
        return email

    def clean_first_name(self):
        return _validate_person_name(self.cleaned_data.get("first_name") or "", field_label=str(_("Имя")))

    def clean_last_name(self):
        return _validate_person_name(self.cleaned_data.get("last_name") or "", field_label=str(_("Фамилия")))

    def clean_phone(self):
        return _validate_phone(self.cleaned_data.get("phone") or "")


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = _("Текущий пароль")
        self.fields["new_password1"].label = _("Новый пароль")
        self.fields["new_password2"].label = _("Повторите новый пароль")
        self.fields["old_password"].widget.attrs.update({"class": "field", "autocomplete": "current-password"})
        self.fields["new_password1"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})
        self.fields["new_password2"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})


class UserPasswordResetForm(PasswordResetForm):
    email = forms.CharField(
        label=_("Email или логин"),
        required=True,
        widget=forms.TextInput(attrs={"class": "field", "autocomplete": "username"}),
        error_messages={
            "required": _("Укажите email или логин."),
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"class": "field"})

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        if not value:
            raise ValidationError(_("Укажите email или логин."))

        if "@" in value:
            return value.lower()

        user = (
            User.objects.filter(username__iexact=value)
            .exclude(email="")
            .order_by("id")
            .first()
        )
        if user and user.email:
            return user.email.strip().lower()
        return value.lower()


class UserSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = _("Новый пароль")
        self.fields["new_password2"].label = _("Повторите новый пароль")
        self.fields["new_password1"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})
        self.fields["new_password2"].widget.attrs.update({"class": "field", "autocomplete": "new-password"})


class OwnerPlaceEditForm(forms.ModelForm):
    draft_save_only = False

    district = forms.ChoiceField(
        label=_("Регион / район"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field"}),
    )
    metro = forms.ChoiceField(
        label=_("Метро"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field"}),
    )
    lat = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-map-coordinate": "lat"}),
    )
    lng = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-map-coordinate": "lng"}),
    )

    class Meta:
        model = Place
        fields = (
            "name_az",
            "name_ru",
            "name_en",
            "description_az",
            "description_ru",
            "description_en",
            "category",
            "subcategory",
            "age_from",
            "age_to",
            "price_from",
            "price_to",
            "district",
            "metro",
            "address",
            "lat",
            "lng",
            "phone1",
            "instagram",
            "website",
            "schedule",
            "lesson_duration_minutes",
            "price_per_lesson",
            "price_per_month",
            "price_per_8_lessons",
            "extra_conditions",
            "additional_info",
            "is_temporary",
            "temporary_start",
            "temporary_end",
            "photo",
        )
        widgets = {
            "name_ru": forms.TextInput(attrs={"class": "field"}),
            "name_az": forms.TextInput(attrs={"class": "field"}),
            "name_en": forms.TextInput(attrs={"class": "field"}),
            "description_ru": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "description_az": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "description_en": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "category": forms.Select(attrs={"class": "field"}),
            "subcategory": forms.TextInput(attrs={"class": "field"}),
            "age_from": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "0"}
            ),
            "age_to": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "18"}
            ),
            "price_from": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "0"}
            ),
            "price_to": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "500"}
            ),
            "address": forms.TextInput(attrs={"class": "field"}),
            "phone1": forms.TextInput(attrs={"class": "field"}),
            "instagram": forms.TextInput(attrs={"class": "field"}),
            "website": forms.URLInput(attrs={"class": "field"}),
            "schedule": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "lesson_duration_minutes": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "60"}
            ),
            "price_per_lesson": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "25"}
            ),
            "price_per_month": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "160"}
            ),
            "price_per_8_lessons": forms.TextInput(
                attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "180"}
            ),
            "extra_conditions": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "additional_info": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "is_temporary": forms.CheckboxInput(attrs={"class": "field-check"}),
            "temporary_start": forms.DateTimeInput(attrs={"class": "field", "type": "datetime-local"}),
            "temporary_end": forms.DateTimeInput(attrs={"class": "field", "type": "datetime-local"}),
            "photo": ImagePreviewFileInput(
                attrs={"class": "field owner-file-uploader-input", "accept": "image/*"}
            ),
        }
        labels = {
            "name_az": _("Название (AZ)"),
            "name_ru": _("Название (RU)"),
            "name_en": _("Название (EN)"),
            "description_az": _("Описание (AZ)"),
            "description_ru": _("Описание (RU)"),
            "description_en": _("Описание (EN)"),
            "category": _("Категория"),
            "subcategory": _("Подкатегория"),
            "age_from": _("Возраст от"),
            "age_to": _("Возраст до"),
            "price_from": _("Цена от"),
            "price_to": _("Цена до"),
            "district": _("Регион / район"),
            "metro": _("Метро"),
            "address": _("Адрес"),
            "phone1": _("Телефон"),
            "instagram": _("Instagram"),
            "website": _("Сайт"),
            "schedule": _("Расписание"),
            "lesson_duration_minutes": _("Длительность урока (мин)"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "extra_conditions": _("Дополнительные условия"),
            "additional_info": _("Дополнительная информация"),
            "is_temporary": _("Временное мероприятие"),
            "temporary_start": _("Начало"),
            "temporary_end": _("Окончание"),
            "photo": _("Основное фото"),
        }

    def __init__(self, *args, **kwargs):
        self.geocoding_check_only = bool(kwargs.pop("geocoding_check_only", False))
        self.draft_save_only = bool(kwargs.pop("draft_save_only", False))
        instance = kwargs.get("instance")
        data = kwargs.get("data")
        if data is not None and instance is not None and getattr(instance, "pk", None):
            missing_lat = "lat" not in data
            missing_lng = "lng" not in data
            if missing_lat or missing_lng:
                mutable_data = data.copy()
                if missing_lat:
                    mutable_data["lat"] = "" if instance.lat is None else str(instance.lat)
                if missing_lng:
                    mutable_data["lng"] = "" if instance.lng is None else str(instance.lng)
                kwargs["data"] = mutable_data
        super().__init__(*args, **kwargs)
        self._configure_location_choices()
        for field_name in ("age_from", "age_to"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Введите возраст числом. Например: 7."),
                    "min_value": _("Возраст не может быть меньше 0."),
                    "max_value": _("Возраст не может быть больше 18."),
                }
            )
        for field_name in ("price_from", "price_to"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Введите цену числом. Например: 120."),
                    "min_value": _("Цена не может быть меньше 0."),
                }
            )
        for field_name in ("price_per_lesson", "price_per_month", "price_per_8_lessons"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Введите цену числом. Например: 120."),
                    "min_value": _("Цена не может быть меньше 0."),
                }
            )
        self.fields["lesson_duration_minutes"].error_messages.update(
            {
                "invalid": _("Введите длительность числом. Например: 60."),
                "min_value": _("Длительность не может быть меньше 0."),
            }
        )
        self.fields["website"].error_messages.update(
            {
                "invalid": _("Укажите корректный адрес сайта. Пример: https://site.com"),
            }
        )
        self.fields["address"].widget.attrs.update(
            {
                "placeholder": _("Улица, дом, ориентир"),
                "autocomplete": "street-address",
            }
        )
        self.fields["address"].help_text = _("Улица, дом, ориентир.")
        self.fields["name_az"].help_text = _("Обязательно для публикации.")
        self.fields["name_ru"].help_text = _("Можно добавить позже.")
        self.fields["name_en"].help_text = _("Можно добавить позже.")
        self.fields["description_az"].help_text = _("Обязательно для публикации.")
        self.fields["description_ru"].help_text = _("Можно добавить позже.")
        self.fields["description_en"].help_text = _("Можно добавить позже.")
        self.fields["schedule"].help_text = _("Например: Пн/Ср/Пт 18:00-19:00.")
        self.fields["lesson_duration_minutes"].help_text = _("Например: 60 минут.")
        self.fields["price_per_lesson"].help_text = _("Если есть отдельная цена.")
        self.fields["price_per_month"].help_text = _("Если есть абонемент.")
        self.fields["price_per_8_lessons"].help_text = _("Если есть пакет занятий.")
        self.fields["extra_conditions"].help_text = _("Скидки, пробный урок, форма.")
        self.fields["additional_info"].help_text = _("Только если есть важные детали.")
        self.fields["photo"].help_text = _("JPG, PNG или WEBP. Максимум 2 МБ.")
        if self.draft_save_only:
            for field in self.fields.values():
                field.required = False
        for field_name in ("temporary_start", "temporary_end"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Укажите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ."),
                }
            )

    def _configure_location_choices(self):
        district_options = []
        metro_options = sort_translated_values(BAKU_METRO_STATIONS)

        try:
            content_settings = CatalogContentSettings.get_solo()
            district_options = sort_translated_values(content_settings.districts())
            metro_options = sort_translated_values(content_settings.metro_stations())
        except Exception:
            # If DB is not available (e.g., management command pre-setup), keep empty options.
            district_options = []

        district_current = (self.initial.get("district") or getattr(self.instance, "district", "") or "").strip()
        metro_current = (self.initial.get("metro") or getattr(self.instance, "metro", "") or "").strip()

        self.fields["district"].choices = self._build_location_choices(
            options=district_options,
            current_value=district_current,
            empty_label=_("Выберите регион или район"),
        )
        self.fields["metro"].choices = self._build_location_choices(
            options=metro_options,
            current_value=metro_current,
            empty_label=_("Выберите метро"),
        )

        self.fields["district"].help_text = _("Выберите регион или район, либо укажите ниже ближайшее метро.")
        self.fields["metro"].help_text = _("Если район не выбран, укажите ближайшую станцию метро.")
        self.fields["district"].error_messages.update({"invalid_choice": _("Выберите регион или район из списка.")})
        self.fields["metro"].error_messages.update({"invalid_choice": _("Выберите станцию метро из списка.")})

    @staticmethod
    def _build_location_choices(*, options, current_value, empty_label):
        choices = [("", empty_label)]
        seen = set()

        for raw in options or []:
            value = str(raw or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            choices.append((value, _(value)))

        if current_value and current_value not in seen:
            choices.insert(1, (current_value, _(current_value)))

        return choices

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("lat")
        lng = cleaned.get("lng")

        if (lat is None) ^ (lng is None):
            message = _("Чтобы отметить место на карте, укажите обе координаты: lat и lng.")
            self.add_error("lat", message)
            self.add_error("lng", message)

        if lat is not None and not -90 <= float(lat) <= 90:
            self.add_error("lat", _("Широта должна быть в диапазоне от -90 до 90."))

        if lng is not None and not -180 <= float(lng) <= 180:
            self.add_error("lng", _("Долгота должна быть в диапазоне от -180 до 180."))

        if self.geocoding_check_only:
            return cleaned

        age_from = cleaned.get("age_from")
        age_to = cleaned.get("age_to")
        if age_from is not None and age_to is not None and age_from > age_to:
            self.add_error(
                "age_to",
                _("Возраст «до» меньше «от». Укажите значение «до», равное или больше «от»."),
            )

        price_from = cleaned.get("price_from")
        price_to = cleaned.get("price_to")
        if price_from is not None and price_to is not None and price_from > price_to:
            self.add_error(
                "price_to",
                _("Цена «до» меньше «от». Укажите верхнюю границу не меньше нижней."),
            )

        temporary = cleaned.get("is_temporary")
        start = cleaned.get("temporary_start")
        end = cleaned.get("temporary_end")
        if temporary:
            if not start:
                self.add_error(
                    "temporary_start",
                    _("Укажите дату и время начала для временного мероприятия."),
                )
            if not end:
                self.add_error(
                    "temporary_end",
                    _("Укажите дату и время окончания для временного мероприятия."),
                )
            if start and end and start > end:
                self.add_error(
                    "temporary_end",
                    _("Дата окончания раньше даты начала. Укажите окончание позже начала."),
                )

        photo = cleaned.get("photo")
        if photo:
            try:
                _validate_uploaded_image(photo)
            except ValidationError as exc:
                self.add_error("photo", exc)

        return cleaned


class OwnerPlaceCreateForm(OwnerPlaceEditForm):
    moderation_note = forms.CharField(
        label=_("Комментарий для модерации"),
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"class": "field", "rows": 2}),
        help_text=_("Если модератору нужен дополнительный контекст."),
    )
    gallery_images = MultipleFileField(
        label=_("Дополнительные фото (до 10)"),
        required=False,
        help_text=_("До 10 фото для галереи, каждое до 2 МБ."),
    )

    class Meta(OwnerPlaceEditForm.Meta):
        fields = OwnerPlaceEditForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gallery_images"].help_text = _("До 10 фото для галереи, каждое до 2 МБ.")
        if self.draft_save_only:
            return
        if self.geocoding_check_only:
            for field_name in self.fields:
                self.fields[field_name].required = field_name == "address"
        else:
            for field_name in (
                "name_az",
                "description_az",
                "category",
                "age_from",
                "age_to",
                "price_from",
                "price_to",
                "address",
                "phone1",
                "photo",
            ):
                self.fields[field_name].required = True

    def clean(self):
        cleaned = super().clean()
        district = (cleaned.get("district") or "").strip()
        metro = (cleaned.get("metro") or "").strip()
        if not self.draft_save_only and not district and not metro:
            message = _("Укажите локацию: выберите район или станцию метро.")
            self.add_error("district", message)
            self.add_error("metro", message)

        if self.geocoding_check_only:
            return cleaned

        if not self.draft_save_only and not (cleaned.get("name_az") or "").strip():
            self.add_error("name_az", _("Укажите основное название на азербайджанском языке."))

        if not self.draft_save_only and not (cleaned.get("description_az") or "").strip():
            self.add_error("description_az", _("Укажите основное описание на азербайджанском языке."))

        gallery_images = self.files.getlist("gallery_images")
        cleaned["gallery_images"] = gallery_images
        if len(gallery_images) > _OWNER_GALLERY_MAX_FILES:
            self.add_error(
                "gallery_images",
                _("Можно загрузить не больше %(limit)s фото.") % {"limit": _OWNER_GALLERY_MAX_FILES},
            )

        for file_obj in gallery_images:
            try:
                _validate_uploaded_image(file_obj)
            except ValidationError as exc:
                self.add_error("gallery_images", exc)
                break

        return cleaned

    def save(self, commit=True):
        place = super().save(commit=False)
        place.name = (
            (self.cleaned_data.get("name_az") or "").strip()
            or (self.cleaned_data.get("name_ru") or "").strip()
            or (self.cleaned_data.get("name_en") or "").strip()
            or place.name
            or "KidsMap"
        )
        if commit:
            place.save()
        return place

class OwnerTeamInvitationForm(forms.Form):
    email = forms.EmailField(
        label=_("Email участника"),
        error_messages={
            "required": _("Укажите email участника."),
            "invalid": _("Укажите корректный email участника. Пример: user@example.com"),
        },
        widget=forms.EmailInput(attrs={"class": "field", "placeholder": "user@example.com"}),
    )
    role = forms.ChoiceField(
        label=_("Роль"),
        choices=UserProfile.OWNER_ROLE_CHOICES,
        initial=UserProfile.OWNER_ROLE_EDITOR,
        error_messages={
            "required": _("Выберите роль участника."),
            "invalid_choice": _("Некорректная роль. Выберите manager, moderator или editor."),
        },
        widget=forms.Select(attrs={"class": "field"}),
    )


class OwnerTeamRoleUpdateForm(forms.Form):
    role = forms.ChoiceField(
        label=_("Роль"),
        choices=UserProfile.OWNER_ROLE_CHOICES,
        error_messages={
            "required": _("Выберите роль участника."),
            "invalid_choice": _("Некорректная роль. Выберите manager, moderator или editor."),
        },
        widget=forms.Select(attrs={"class": "field"}),
    )
