from __future__ import annotations

import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import Place, UserProfile


User = get_user_model()
_NAME_CONNECTORS = {" ", "-", "'"}
_PHONE_RE = re.compile(r"^\+?[0-9()\-\s]{7,25}$")


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
    role = forms.ChoiceField(
        label=_("Кто вы?"),
        choices=UserProfile.ROLE_CHOICES,
        initial=UserProfile.ROLE_USER,
        error_messages={
            "required": _("Выберите тип аккаунта: обычный пользователь или владелец кружка."),
            "invalid_choice": _("Некорректный тип аккаунта. Выберите один из предложенных вариантов."),
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
        self.fields["email"].help_text = _("Укажите рабочий email: на него может прийти важная информация.")
        self.fields["phone"].help_text = _("Номер нужен для связи по вашему аккаунту.")
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
        label=_("Логин"),
        error_messages={
            "required": _("Укажите логин."),
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


class UserProfileEditForm(forms.Form):
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


class OwnerPlaceEditForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = (
            "name_ru",
            "name_az",
            "name_en",
            "description_ru",
            "description_az",
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
            "phone1",
            "instagram",
            "website",
            "schedule",
            "is_temporary",
            "temporary_start",
            "temporary_end",
            "cover_photo",
            "photo",
        )
        widgets = {
            "name_ru": forms.TextInput(attrs={"class": "field"}),
            "name_az": forms.TextInput(attrs={"class": "field"}),
            "name_en": forms.TextInput(attrs={"class": "field"}),
            "description_ru": forms.Textarea(attrs={"class": "field", "rows": 3}),
            "description_az": forms.Textarea(attrs={"class": "field", "rows": 3}),
            "description_en": forms.Textarea(attrs={"class": "field", "rows": 3}),
            "category": forms.Select(attrs={"class": "field"}),
            "subcategory": forms.TextInput(attrs={"class": "field"}),
            "age_from": forms.NumberInput(attrs={"class": "field", "min": 0, "max": 18}),
            "age_to": forms.NumberInput(attrs={"class": "field", "min": 0, "max": 18}),
            "price_from": forms.NumberInput(attrs={"class": "field", "min": 0}),
            "price_to": forms.NumberInput(attrs={"class": "field", "min": 0}),
            "district": forms.TextInput(attrs={"class": "field"}),
            "metro": forms.TextInput(attrs={"class": "field"}),
            "address": forms.TextInput(attrs={"class": "field"}),
            "phone1": forms.TextInput(attrs={"class": "field"}),
            "instagram": forms.TextInput(attrs={"class": "field"}),
            "website": forms.URLInput(attrs={"class": "field"}),
            "schedule": forms.Textarea(attrs={"class": "field", "rows": 2}),
            "is_temporary": forms.CheckboxInput(attrs={"class": "field-check"}),
            "temporary_start": forms.DateTimeInput(attrs={"class": "field", "type": "datetime-local"}),
            "temporary_end": forms.DateTimeInput(attrs={"class": "field", "type": "datetime-local"}),
            "cover_photo": forms.ClearableFileInput(attrs={"class": "field"}),
            "photo": forms.ClearableFileInput(attrs={"class": "field"}),
        }
        labels = {
            "name_ru": _("Название (RU)"),
            "name_az": _("Название (AZ)"),
            "name_en": _("Название (EN)"),
            "description_ru": _("Описание (RU)"),
            "description_az": _("Описание (AZ)"),
            "description_en": _("Описание (EN)"),
            "category": _("Категория"),
            "subcategory": _("Подкатегория"),
            "age_from": _("Возраст от"),
            "age_to": _("Возраст до"),
            "price_from": _("Цена от"),
            "price_to": _("Цена до"),
            "district": _("Район"),
            "metro": _("Метро"),
            "address": _("Адрес"),
            "phone1": _("Телефон"),
            "instagram": _("Instagram"),
            "website": _("Сайт"),
            "schedule": _("Расписание"),
            "is_temporary": _("Временное мероприятие"),
            "temporary_start": _("Начало"),
            "temporary_end": _("Окончание"),
            "cover_photo": _("Фото для шапки"),
            "photo": _("Основное фото"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.fields["website"].error_messages.update(
            {
                "invalid": _("Укажите корректный адрес сайта. Пример: https://site.com"),
            }
        )
        for field_name in ("temporary_start", "temporary_end"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Укажите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ."),
                }
            )

    def clean(self):
        cleaned = super().clean()
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
        if temporary and start and end and start > end:
            self.add_error(
                "temporary_end",
                _("Дата окончания раньше даты начала. Укажите окончание позже начала."),
            )

        return cleaned


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
