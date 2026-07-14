from __future__ import annotations

from datetime import datetime
import hashlib
import json
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
from django.utils.text import slugify
from django.utils import timezone
from django.utils.translation import get_language, gettext as translate, gettext_lazy as _

from catalog.content_data import BAKU_METRO_STATIONS
from catalog.models import CatalogContentSettings, Event, Place, UserProfile, Category, Subcategory, Specialist, SpecialistSpecialization, Region, District, MetroStation
from catalog.services.place_schedule import (
    dump_schedule_payload,
    is_meaningful_schedule,
    serialize_place_schedule,
    validate_schedule_payload,
)
from catalog.services.options import sort_translated_values
from catalog.services.pricing_plans import normalize_pricing_plans

try:
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat
except ImportError:  # pragma: no cover - dependency should be installed in normal runtime
    phonenumbers = None
    NumberParseException = Exception
    PhoneNumberFormat = None


User = get_user_model()
_NAME_CONNECTORS = {" ", "-", "'"}
_PHONE_RE = re.compile(r"^\+?[0-9()\-\s]{7,25}$")
_OWNER_IMAGE_MAX_BYTES = 2 * 1024 * 1024
_OWNER_GALLERY_MAX_FILES = 10


class LocalizedModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if hasattr(obj, "name_i18n"):
            return obj.name_i18n(get_language())
        return super().label_from_instance(obj)


class SubcategorySelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option.setdefault("attrs", {})
            option["attrs"]["data-category"] = instance.category_id
            option["attrs"]["data-label-az"] = instance.name_i18n("az")
            option["attrs"]["data-label-ru"] = instance.name_i18n("ru")
            option["attrs"]["data-label-en"] = instance.name_i18n("en")
        return option


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleFileField, self).clean(file_item, initial) for file_item in files]


class PlaceScheduleEditorFormMixin:
    def _init_schedule_editor(self):
        from catalog.services.place_schedule import parse_schedule_payload
        if "structured_schedule" not in self.fields:
            self.fields["structured_schedule"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(attrs={"data-km-schedule-editor-input": "1"}),
            )
        instance = getattr(self, "instance", None)
        payload = serialize_place_schedule(instance) if instance is not None else []
        raw_value = self.data.get("structured_schedule") if getattr(self, "is_bound", False) else None

        if not raw_value:
            raw_value = dump_schedule_payload(payload)
        else:
            payload = parse_schedule_payload(raw_value)

        self.fields["structured_schedule"].initial = raw_value
        self.schedule_editor_payload = raw_value
        self.schedule_editor_errors = {}
        self.cleaned_schedule_days = payload
        self.schedule_editor_days = [
            {
                "weekday": day["weekday"],
                "is_closed": day["is_closed"],
                "is_24_hours": day["is_24_hours"],
                "intervals": day["intervals"],
                "errors": [],
            }
            for day in payload
        ]
        self.schedule_legacy_value = (getattr(instance, "schedule", "") or "").strip()
        self.fields["schedule"].widget = forms.HiddenInput()

    def _clean_schedule_editor(self, cleaned):
        raw_value = cleaned.get("structured_schedule") or self.data.get("structured_schedule") or self.fields["structured_schedule"].initial or ""
        validation = validate_schedule_payload(raw_value)
        self.schedule_editor_payload = raw_value
        self.schedule_editor_errors = validation.errors
        self.cleaned_schedule_days = validation.days
        self.schedule_editor_days = [
            {
                "weekday": day["weekday"],
                "is_closed": day["is_closed"],
                "is_24_hours": day["is_24_hours"],
                "intervals": day["intervals"],
                "errors": validation.errors.get(day["weekday"], []),
            }
            for day in validation.days
        ]

        if validation.errors:
            self.add_error("structured_schedule", _("Проверьте расписание работы."))

        cleaned["structured_schedule"] = dump_schedule_payload(validation.days)
        return cleaned

    def save_schedule(self, place):
        from catalog.services.place_schedule import sync_place_schedule

        sync_place_schedule(place, self.cleaned_schedule_days)


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _validate_person_name(value: str, *, field_label: str) -> str:
    normalized = _normalize_whitespace(value)
    language = (get_language() or "ru").split("-")[0]
    if not normalized:
        if language == "az":
            raise ValidationError("%(field)s daxil edilməlidir." % {"field": field_label})
        raise ValidationError(_("%(field)s обязательно для заполнения.") % {"field": field_label})
    if len(normalized) < 2:
        if language == "az":
            raise ValidationError("%(field)s çox qısadır. Ən azı 2 simvol daxil edin." % {"field": field_label})
        raise ValidationError(_("%(field)s слишком короткое. Укажите минимум 2 символа.") % {"field": field_label})
    if normalized[0] in _NAME_CONNECTORS or normalized[-1] in _NAME_CONNECTORS:
        if language == "az":
            raise ValidationError("%(field)s daxilində uyğun olmayan simvollar var." % {"field": field_label})
        raise ValidationError(_("%(field)s содержит недопустимые символы.") % {"field": field_label})
    for char in normalized:
        if char in _NAME_CONNECTORS or char.isalpha():
            continue
        if language == "az":
            raise ValidationError(
                "%(field)s yalnız hərflər, boşluq, defis və ya apostrofdan ibarət olmalıdır."
                % {"field": field_label}
            )
        raise ValidationError(
            _("%(field)s должно содержать только буквы, пробел, дефис или апостроф.")
            % {"field": field_label}
        )
    return normalized


def _validate_phone(value: str) -> str:
    normalized = _normalize_whitespace(value)
    language = (get_language() or "ru").split("-")[0]
    if not normalized:
        if language == "az":
            raise ValidationError("Mobil nömrənizi daxil edin.")
        raise ValidationError(_("Укажите номер телефона."))
    if not _PHONE_RE.fullmatch(normalized):
        if language == "az":
            raise ValidationError("Düzgün telefon nömrəsi daxil edin. Nümunə: +994 50 123 45 67")
        raise ValidationError(_("Введите корректный номер телефона. Пример: +994 50 123 45 67"))
    digits = "".join(char for char in normalized if char.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        if language == "az":
            raise ValidationError("Telefon nömrəsi 7-dən 15-ə qədər rəqəmdən ibarət olmalıdır.")
        raise ValidationError(_("Номер телефона должен содержать от 7 до 15 цифр."))
    return normalized


def _normalize_azerbaijan_phone_candidate(value: str) -> str:
    normalized = _normalize_whitespace(value)
    if normalized.startswith("00"):
        normalized = f"+{normalized[2:]}"
    return normalized


def _azerbaijan_phone_error() -> ValidationError:
    language = (get_language() or "ru").split("-")[0]
    if language == "az":
        return ValidationError("Azərbaycan nömrəsini düzgün daxil edin. Nümunə: +994 50 123 45 67")
    if language == "en":
        return ValidationError("Enter a valid Azerbaijan phone number. Example: +994 50 123 45 67")
    return ValidationError(_("Укажите корректный номер Азербайджана. Пример: +994 50 123 45 67"))


def _format_azerbaijan_phone_for_input(value: str) -> str:
    normalized = _normalize_azerbaijan_phone_candidate(value)
    if not normalized:
        return ""

    if phonenumbers is not None:
        try:
            parsed = phonenumbers.parse(normalized, "AZ")
        except NumberParseException:
            parsed = None
        if parsed and parsed.country_code == 994 and phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

    digits = "".join(char for char in normalized if char.isdigit())
    if digits.startswith("994"):
        national = digits[3:]
    elif digits.startswith("0"):
        national = digits[1:]
    else:
        national = digits

    national = national[:9]
    if not national:
        return ""

    chunks = []
    for start, end in ((0, 2), (2, 5), (5, 7), (7, 9)):
        part = national[start:end]
        if part:
            chunks.append(part)
    return "+994 " + " ".join(chunks)


def _validate_azerbaijan_phone(value: str, *, required: bool = False) -> str:
    normalized = _normalize_azerbaijan_phone_candidate(value)
    if not normalized:
        if required:
            language = (get_language() or "ru").split("-")[0]
            if language == "az":
                raise ValidationError("Telefon nömrəsini daxil edin.")
            if language == "en":
                raise ValidationError("Enter the phone number.")
            raise ValidationError(_("Укажите номер телефона."))
        return ""

    if phonenumbers is not None:
        try:
            parsed = phonenumbers.parse(normalized, "AZ")
        except NumberParseException as exc:
            raise _azerbaijan_phone_error() from exc
        if parsed.country_code != 994:
            raise _azerbaijan_phone_error()
        national = str(parsed.national_number)
        if len(national) != 9 or not national.isdigit() or not phonenumbers.is_possible_number(parsed):
            raise _azerbaijan_phone_error()
        return f"+994{national}"

    digits = "".join(char for char in normalized if char.isdigit())
    if digits.startswith("994"):
        national = digits[3:]
    elif digits.startswith("0"):
        national = digits[1:]
    else:
        national = digits

    if len(national) != 9 or not national.isdigit():
        raise _azerbaijan_phone_error()
    return f"+994{national}"


def _build_registration_username(email: str) -> str:
    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return ""

    if "@" in normalized_email:
        local_part, domain_part = normalized_email.split("@", 1)
    else:
        local_part, domain_part = normalized_email, "kidsmap.az"

    local_slug = slugify(local_part.replace(".", " ").replace("_", " ").replace("+", " "), allow_unicode=False)
    local_slug = local_slug.replace("-", "_") or "user"
    domain_slug = slugify(domain_part.replace(".", " "), allow_unicode=False).replace("-", "_") or "kidsmap"
    digest = hashlib.sha1(normalized_email.encode("utf-8")).hexdigest()[:10]
    candidate = f"{local_slug}_{domain_slug}_{digest}"[:150]
    if not User.objects.filter(username__iexact=candidate).exists():
        return candidate

    base = candidate[:138].rstrip("_") or "user"
    suffix = 2
    while True:
        value = f"{base}_{suffix}"[:150]
        if not User.objects.filter(username__iexact=value).exists():
            return value
        suffix += 1


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
    agreement = forms.BooleanField(
        label=_("Я согласен с правилами и политикой конфиденциальности."),
        required=True,
        error_messages={
            "required": _("Подтвердите согласие с правилами и политикой конфиденциальности."),
        },
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("first_name", "last_name", "email", "phone", "password1", "password2"):
            existing_class = self.fields[field_name].widget.attrs.get("class", "")
            self.fields[field_name].widget.attrs["class"] = f"{existing_class} register-field-input".strip()
        self.fields["first_name"].help_text = _("Введите ваше настоящее имя.")
        self.fields["last_name"].help_text = _("Введите вашу настоящую фамилию.")
        self.fields["email"].help_text = _(
            "Укажите рабочий email: после регистрации на него придет код подтверждения."
        )
        self.fields["phone"].help_text = _("Номер нужен для связи по вашему аккаунту.")
        self.fields["email"].widget.attrs["inputmode"] = "email"
        self.fields["phone"].widget.attrs["inputmode"] = "tel"
        self.fields["password1"].widget.attrs.update({"class": "field register-field-input", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"class": "field register-field-input", "autocomplete": "new-password"})
        self.fields["agreement"].widget.attrs["class"] = "register-consent-checkbox"
        self.fields["password1"].label = _("Пароль")
        self.fields["password2"].label = _("Повторите пароль")
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
        self.fields["password1"].error_messages.update(
            {"required": _("Придумайте пароль, чтобы продолжить регистрацию.")}
        )
        self.fields["password2"].error_messages.update(
            {"required": _("Повторите пароль, чтобы подтвердить ввод.")}
        )
        self._apply_registration_copy()

    def _apply_registration_copy(self) -> None:
        language = (get_language() or "az").split("-")[0]
        placeholders = {
            "first_name": {
                "az": "Adınızı daxil edin",
                "en": "Enter your first name",
                "ru": "Введите имя",
            },
            "last_name": {
                "az": "Soyadınızı daxil edin",
                "en": "Enter your last name",
                "ru": "Введите фамилию",
            },
            "email": {
                "az": "E-poçt ünvanınızı daxil edin",
                "en": "Enter your email address",
                "ru": "Введите email",
            },
            "phone": {
                "az": "Mobil nömrənizi daxil edin",
                "en": "Enter your mobile number",
                "ru": "Введите номер телефона",
            },
            "password1": {
                "az": "Şifrənizi daxil edin",
                "en": "Enter your password",
                "ru": "Введите пароль",
            },
            "password2": {
                "az": "Şifrənizi yenidən daxil edin",
                "en": "Re-enter your password",
                "ru": "Повторите пароль",
            },
        }
        for field_name, variants in placeholders.items():
            self.fields[field_name].widget.attrs["placeholder"] = variants.get(language, variants["ru"])

        if language != "az":
            return

        self.fields["first_name"].label = "Ad"
        self.fields["last_name"].label = "Soyad"
        self.fields["email"].label = "E-poçt"
        self.fields["phone"].label = "Telefon"
        self.fields["password1"].label = "Şifrə"
        self.fields["password2"].label = "Şifrəni təkrarlayın"
        self.fields["agreement"].label = "Qaydalar və Şəxsi məlumatların mühafizəsi siyasəti ilə razıyam."
        self.fields["first_name"].help_text = ""
        self.fields["last_name"].help_text = ""
        self.fields["email"].help_text = ""
        self.fields["phone"].help_text = ""
        self.fields["first_name"].error_messages["required"] = "Adınızı daxil edin."
        self.fields["last_name"].error_messages["required"] = "Soyadınızı daxil edin."
        self.fields["email"].error_messages.update(
            {
                "required": "E-poçt ünvanınızı daxil edin.",
                "invalid": "Düzgün e-poçt ünvanı daxil edin.",
            }
        )
        self.fields["phone"].error_messages["required"] = "Mobil nömrənizi daxil edin."
        self.fields["password1"].error_messages["required"] = "Şifrəni daxil edin."
        self.fields["password2"].error_messages["required"] = "Şifrəni yenidən daxil edin."
        self.fields["agreement"].error_messages["required"] = (
            "Qaydalar və məxfilik siyasəti ilə razı olduğunuzu təsdiqləyin."
        )
        self.error_messages["password_mismatch"] = "Şifrələr eyni deyil. Hər iki xanada eyni şifrəni yazın."

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
        user.username = _build_registration_username(self.cleaned_data["email"])
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
        "inactive": _("Email не подтвержден. Подтвердите email кодом из письма, затем повторите вход."),
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

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "register-field-input",
                "autocomplete": "username",
                "inputmode": "email",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "register-field-input",
                "autocomplete": "current-password",
            }
        )
        self.fields["remember_me"].widget.attrs.update({"class": "register-consent-checkbox"})
        self._apply_login_copy()

    def _apply_login_copy(self) -> None:
        language = (get_language() or "ru").split("-")[0]
        if language == "az":
            self.fields["username"].label = "E-poçt"
            self.fields["username"].widget.attrs["placeholder"] = "E-poçt ünvanınızı daxil edin"
            self.fields["username"].error_messages.update(
                {
                    "required": "E-poçt ünvanı tələb olunur.",
                    "invalid": "Düzgün e-poçt ünvanı daxil edin.",
                }
            )
            self.fields["password"].label = "Şifrə"
            self.fields["password"].widget.attrs["placeholder"] = "Şifrənizi daxil edin"
            self.fields["password"].error_messages["required"] = "Şifrə tələb olunur."
            self.fields["remember_me"].label = "Məni xatırla"
            self.error_messages["invalid_login"] = "E-poçt və ya şifrə yanlışdır."
            self.error_messages["inactive"] = "Bu hesab aktivləşdirilməyib. E-poçtunuzu yoxlayın."
            return

        if language == "en":
            self.fields["username"].label = "Email"
            self.fields["username"].widget.attrs["placeholder"] = "Enter your email address"
            self.fields["username"].error_messages["required"] = "Enter your email."
            self.fields["password"].label = "Password"
            self.fields["password"].widget.attrs["placeholder"] = "Enter your password"
            self.fields["password"].error_messages["required"] = "Enter your password."
            self.fields["remember_me"].label = "Remember me"
            self.error_messages["invalid_login"] = "Incorrect email or password."
            self.error_messages["inactive"] = "This account has not been verified yet. Check your email."
            return

        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs["placeholder"] = "Введите email"
        self.fields["username"].error_messages["required"] = "Укажите email."
        self.fields["password"].widget.attrs["placeholder"] = "Введите пароль"
        self.error_messages["inactive"] = "Email не подтвержден. Подтвердите email кодом из письма, затем повторите вход."

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
                self.error_messages["inactive"],
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
                    self.error_messages["inactive"],
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


class OwnerPlaceEditForm(PlaceScheduleEditorFormMixin, forms.ModelForm):
    pricing_plans = forms.CharField(required=False, widget=forms.HiddenInput())
    lesson_format = forms.ChoiceField(required=False, choices=Place.LESSON_FORMAT_CHOICES, widget=forms.Select(attrs={"class": "field"}))
    draft_save_only = False
    submit_for_moderation = False
    coordinate_refresh_only = False
    require_location_region = False
    require_schedule_for_publish = False

    region = forms.ChoiceField(
        label=_("Город / регион"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-region": ""}),
    )
    district = forms.ChoiceField(
        label=_("Район города"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-district": ""}),
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
            "region",
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
            "lesson_format",
            "lessons_per_week",
            "lessons_per_month",
            "price_per_lesson",
            "price_per_month",
            "price_per_8_lessons",
            "pricing_plans",
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
            "subcategory": SubcategorySelect(attrs={"class": "field"}),
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
            "lessons_per_week": forms.NumberInput(attrs={"class": "field", "min": "1", "placeholder": "2"}),
            "lessons_per_month": forms.NumberInput(attrs={"class": "field", "min": "1", "placeholder": "8"}),
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
            "temporary_start": forms.TextInput(
                attrs={
                    "class": "field",
                    "data-kidsmap-datetime-picker": "1",
                    "data-allow-input": "1",
                    "placeholder": _("Время начала"),
                }
            ),
            "temporary_end": forms.TextInput(
                attrs={
                    "class": "field",
                    "data-kidsmap-datetime-picker": "1",
                    "data-allow-input": "1",
                    "placeholder": _("Время окончания"),
                }
            ),
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
            "lesson_format": _("Формат занятий"),
            "lessons_per_week": _("Занятий в неделю"),
            "lessons_per_month": _("Занятий в месяц"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "pricing_plans": _("Тарифы"),
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
        self.submit_for_moderation = bool(kwargs.pop("submit_for_moderation", False))
        self.coordinate_refresh_only = bool(kwargs.pop("coordinate_refresh_only", False))
        instance = kwargs.get("instance")
        data = kwargs.get("data")
        if data is not None:
            from catalog.services.locations import normalize_to_key

            mutable_data = data.copy()
            region_value = (mutable_data.get("region") or "").strip()
            district_value = (mutable_data.get("district") or "").strip()
            metro_value = (mutable_data.get("metro") or "").strip()
            normalized_district = normalize_to_key(district_value)

            if district_value and normalized_district != district_value:
                mutable_data["district"] = normalized_district
                district_value = normalized_district

            if not region_value and (district_value.startswith("baku_") or metro_value):
                mutable_data["region"] = "baku"

            kwargs["data"] = mutable_data
            data = mutable_data
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

        if "pricing_plans" in self.fields:
            current_plans = getattr(instance, "pricing_plans", None) if instance is not None else None
            if not self.is_bound and current_plans:
                self.initial["pricing_plans"] = json.dumps(current_plans, ensure_ascii=False)

        if self.submit_for_moderation:
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

        from catalog.services.locations import init_location_fields
        init_location_fields(self, instance)

        if "category" in self.fields:
            qs = Category.objects.filter(is_active=True)
            if instance and getattr(instance, "category_id", None):
                qs = Category.objects.filter(Q(is_active=True) | Q(code=instance.category_id))
            self.fields["category"].queryset = qs.order_by("order", "name_ru", "name")
            self.fields["category"].label_from_instance = lambda obj: obj.name_i18n(get_language())
            
        if "subcategory" in self.fields:
            qs = Subcategory.objects.filter(is_active=True)
            if instance and getattr(instance, "subcategory_id", None):
                qs = Subcategory.objects.filter(Q(is_active=True) | Q(id=instance.subcategory_id))
            self.fields["subcategory"].queryset = qs.select_related("category").order_by("category__order", "order", "name_ru", "name")
            self.fields["subcategory"].label_from_instance = lambda obj: obj.name_i18n(get_language())
            self._coerce_bound_subcategory_value()

        self.fields["temporary_start"].input_formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
        self.fields["temporary_end"].input_formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
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
        self.fields["phone1"].widget.attrs.update(
            {
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+994 50 123 45 67",
                "data-km-az-phone": "1",
                "maxlength": "20",
            }
        )
        phone_value = self.initial.get("phone1") or getattr(self.instance, "phone1", "") or ""
        if phone_value:
            self.initial["phone1"] = _format_azerbaijan_phone_for_input(phone_value)
        self.fields["address"].help_text = _("Улица, дом, ориентир.")
        self.fields["name_az"].help_text = _("Обязательно для публикации.")
        self.fields["name_ru"].help_text = _("Можно добавить позже.")
        self.fields["name_en"].help_text = _("Можно добавить позже.")
        self.fields["description_az"].help_text = _("Обязательно для публикации.")
        self.fields["description_ru"].help_text = _("Можно добавить позже.")
        self.fields["description_en"].help_text = _("Можно добавить позже.")
        self.fields["schedule"].help_text = _("Например: Пн/Ср/Пт 18:00-19:00.")
        self.fields["lesson_duration_minutes"].help_text = _("Например: 60 минут.")
        current_language = (get_language() or "ru").split("-")[0]
        if current_language == "az":
            free_price_hint = "Pulsuzdursa, 0 yazın."
            free_range_hint = "Məkan pulsuzdursa, hər iki sahədə 0 yazın."
        elif current_language == "en":
            free_price_hint = "Enter 0 if it is free."
            free_range_hint = "Enter 0 in both fields if the place is free."
        else:
            free_price_hint = "Если бесплатно, укажите 0."
            free_range_hint = "Если место бесплатное, укажите 0 в обоих полях."
        self.fields["price_from"].help_text = free_range_hint
        self.fields["price_to"].help_text = free_range_hint
        self.fields["price_per_lesson"].help_text = f"{_('Если есть отдельная цена.')} {free_price_hint}"
        self.fields["price_per_month"].help_text = f"{_('Если есть абонемент.')} {free_price_hint}"
        self.fields["price_per_8_lessons"].help_text = f"{_('Если есть пакет занятий.')} {free_price_hint}"
        self.fields["extra_conditions"].help_text = _("Скидки, пробный урок, форма.")
        self.fields["additional_info"].help_text = _("Только если есть важные детали.")
        self.fields["photo"].help_text = _("JPG, PNG или WEBP до 2 МБ. В каталоге главное фото показывается квадратом.")
        if self.draft_save_only:
            for field in self.fields.values():
                field.required = False
        for field_name in ("temporary_start", "temporary_end"):
            self.fields[field_name].error_messages.update(
                {
                    "invalid": _("Укажите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ."),
                }
            )
        self._init_schedule_editor()

    def _configure_location_choices(self):
        from catalog.services.locations import configure_location_choices
        configure_location_choices(self)

        default_metro_options = sort_translated_values(BAKU_METRO_STATIONS)
        metro_options = default_metro_options
        try:
            content_settings = CatalogContentSettings.get_solo()
            metro_options = sort_translated_values(content_settings.metro_stations())
        except Exception:
            pass

        metro_current = (
            (self.data.get("metro") if getattr(self, "is_bound", False) else "")
            or self.initial.get("metro")
            or getattr(self.instance, "metro", "")
            or ""
        ).strip()
        allow_current_metro = (
            self.geocoding_check_only
            or bool(getattr(self.instance, "pk", None))
            or metro_current in BAKU_METRO_STATIONS
        )
        if allow_current_metro and metro_current and metro_current not in metro_options:
            metro_options = [metro_current, *metro_options]

        self.fields["metro"].choices = self._build_location_choices(
            options=metro_options,
            current_value=metro_current,
            empty_label=_("Выберите метро"),
            include_current=allow_current_metro,
        )
        self.fields["metro"].help_text = _("Если район не выбран, укажите ближайшую станцию метро.")
        self.fields["metro"].error_messages.update({"invalid_choice": _("Выберите станцию метро из списка.")})

    @staticmethod
    def _build_location_choices(*, options, current_value, empty_label, include_current=True):
        choices = [("", empty_label)]
        seen = set()

        for raw in options or []:
            value = str(raw or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            choices.append((value, translate(value)))

        if include_current and current_value and current_value not in seen:
            choices.insert(1, (current_value, translate(current_value)))

        return choices

    def _coerce_bound_subcategory_value(self):
        if not getattr(self, "is_bound", False):
            return
        raw_value = str(self.data.get("subcategory") or "").strip()
        if not raw_value or raw_value.isdigit():
            return

        category_id = str(self.data.get("category") or "").strip()
        lookup = (
            Q(name__iexact=raw_value)
            | Q(name_ru__iexact=raw_value)
            | Q(name_az__iexact=raw_value)
            | Q(name_en__iexact=raw_value)
        )
        queryset = Subcategory.objects.filter(is_active=True).filter(lookup)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        subcategory = queryset.order_by("order", "id").first()

        mutable_data = self.data.copy()
        mutable_data["subcategory"] = str(subcategory.pk) if subcategory else ""
        self.data = mutable_data

    def clean(self):
        cleaned = super().clean()
        cleaned = self._clean_schedule_editor(cleaned)

        try:
            cleaned["pricing_plans"] = normalize_pricing_plans(cleaned.get("pricing_plans") or "[]")
        except ValidationError as exc:
            self.add_error("pricing_plans", exc)
            cleaned["pricing_plans"] = []
        
        from catalog.services.locations import clean_location_fields
        cleaned = clean_location_fields(self, cleaned)

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

        category = cleaned.get("category")
        subcategory = cleaned.get("subcategory")
        if category and subcategory:
            if subcategory.category_id != category.pk:
                self.add_error(
                    "subcategory", 
                    _("Выбранная подкатегория не принадлежит к указанной категории.")
                )

        if self.geocoding_check_only:
            return cleaned

        if (
            not self.draft_save_only
            and not self.coordinate_refresh_only
            and self.submit_for_moderation
            and not (lat is not None and lng is not None)
            and not cleaned.get("is_temporary")
            and not (cleaned.get("schedule") or "").strip()
            and not is_meaningful_schedule(self.cleaned_schedule_days)
        ):
            self.add_error("structured_schedule", _("Укажите, когда место работает."))

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

        if self.submit_for_moderation:
            district = (cleaned.get("district") or "").strip()
            metro = (cleaned.get("metro") or "").strip()
            if not district and not metro:
                message = _("Укажите локацию: выберите район или станцию метро.")
                self.add_error("district", message)
                self.add_error("metro", message)

        photo = cleaned.get("photo")
        if photo:
            try:
                _validate_uploaded_image(photo)
            except ValidationError as exc:
                self.add_error("photo", exc)

        return cleaned

    def clean_phone1(self):
        value = self.cleaned_data.get("phone1") or ""
        if not value:
            return ""
        return _validate_azerbaijan_phone(value, required=False)


class OwnerPlaceCreateForm(OwnerPlaceEditForm):
    require_location_region = True
    require_schedule_for_publish = True

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
        kwargs.setdefault("submit_for_moderation", not kwargs.get("draft_save_only", False))
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

    def clean_phone1(self):
        value = self.cleaned_data.get("phone1") or ""
        if (self.draft_save_only or self.geocoding_check_only) and not value:
            return ""
        return _validate_azerbaijan_phone(
            value,
            required=not self.draft_save_only and not self.geocoding_check_only,
        )

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


class OwnerEventForm(forms.ModelForm):
    draft_save_only = False
    require_location_region = False

    region = forms.ChoiceField(
        label=_("Город / регион"), required=False, choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-region": ""}),
    )
    district = forms.ChoiceField(
        label=_("Район города"), required=False, choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-district": ""}),
    )
    metro = forms.ChoiceField(
        label=_("Метро"), required=False, choices=(), widget=forms.Select(attrs={"class": "field"}),
    )

    event_date = forms.DateField(
        label=_("Дата"),
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.TextInput(
            attrs={
                "class": "field",
                "data-kidsmap-date-picker": "1",
                "data-min-today": "1",
                "data-allow-input": "1",
                "placeholder": _("Выберите дату"),
            }
        ),
    )
    start_time_input = forms.TimeField(
        label=_("Время начала"),
        required=False,
        input_formats=["%H:%M"],
        widget=forms.TextInput(
            attrs={
                "class": "field",
                "data-kidsmap-time-picker": "1",
                "data-allow-input": "1",
                "placeholder": _("Выберите время"),
            }
        ),
    )
    end_date = forms.DateField(
        label=_("Дата окончания"),
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.TextInput(
            attrs={
                "class": "field",
                "data-kidsmap-date-picker": "1",
                "data-min-today": "1",
                "data-allow-input": "1",
                "placeholder": _("Выберите дату"),
            }
        ),
    )
    end_time_input = forms.TimeField(
        label=_("Время окончания"),
        required=False,
        input_formats=["%H:%M"],
        widget=forms.TextInput(
            attrs={
                "class": "field",
                "data-kidsmap-time-picker": "1",
                "data-allow-input": "1",
                "placeholder": _("Выберите время"),
            }
        ),
    )

    related_place = forms.ModelChoiceField(
        label=_("Связанное место"),
        required=False,
        queryset=Place.objects.none(),
        widget=forms.Select(attrs={"class": "field", "data-event-related-place": "1"}),
        help_text=_("Необязательно. Можно добавить мероприятие без постоянного места."),
    )

    class Meta:
        model = Event
        fields = (
            "name_az",
            "category",
            "start_datetime",
            "end_datetime",
            "age_from",
            "age_to",
            "price_text",
            "related_place",
            "region",
            "district",
            "metro",
            "address",
            "lat",
            "lng",
            "phone",
            "description_az",
            "photo",
            "moderation_note",
        )
        widgets = {
            "name_az": forms.TextInput(attrs={"class": "field", "placeholder": _("Например: мастер-класс по рисованию")}),
            "category": forms.Select(attrs={"class": "field"}),
            "start_datetime": forms.HiddenInput(),
            "end_datetime": forms.HiddenInput(),
            "age_from": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "6"}),
            "age_to": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "12"}),
            "price_text": forms.TextInput(attrs={"class": "field", "placeholder": _("Например: 15 AZN или бесплатно")}),
            "address": forms.TextInput(attrs={"class": "field", "placeholder": _("Например: Bakı, Nərimanov r., Xətai pr. 12")}),
            "lat": forms.HiddenInput(),
            "lng": forms.HiddenInput(),
            "phone": forms.TextInput(attrs={"class": "field", "placeholder": _("Например: 050 123 45 67")}),
            "description_az": forms.Textarea(
                attrs={
                    "class": "field",
                    "rows": 5,
                    "maxlength": "300",
                    "placeholder": _("Qısa məlumat: tədbirdə nələr olacaq, kimlər üçün uyğundur."),
                    "data-counter-target": "event-description-counter",
                }
            ),
            "photo": ImagePreviewFileInput(
                attrs={"class": "field owner-file-uploader-input", "accept": "image/*"}
            ),
            "moderation_note": forms.Textarea(attrs={"class": "field", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.draft_save_only = bool(kwargs.pop("draft_save_only", False))
        super().__init__(*args, **kwargs)
        self.fields["start_datetime"].input_formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
        self.fields["end_datetime"].input_formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
        if self.instance and getattr(self.instance, "pk", None):
            if self.instance.start_datetime:
                localized_start = timezone.localtime(self.instance.start_datetime)
                self.fields["event_date"].initial = localized_start.date()
                self.fields["start_time_input"].initial = localized_start.strftime("%H:%M")
            if self.instance.end_datetime:
                localized_end = timezone.localtime(self.instance.end_datetime)
                self.fields["end_date"].initial = localized_end.date()
                self.fields["end_time_input"].initial = localized_end.strftime("%H:%M")
        if self.user is not None and getattr(self.user, "is_authenticated", False):
            self.fields["related_place"].queryset = (
                Place.objects.filter(owner=self.user, deleted_at__isnull=True)
                .exclude(status=Place.STATUS_REJECTED)
                .order_by("name_az", "name_ru", "name")
            )
        self.fields["photo"].help_text = _("JPG, PNG или WEBP. Максимум 2 МБ.")
        self.fields["moderation_note"].help_text = _("Необязательно. Укажите детали для модератора.")
        from catalog.services.locations import configure_location_choices, init_location_fields
        init_location_fields(self, self.instance)
        configure_location_choices(self)
        if self.draft_save_only:
            for field in self.fields.values():
                field.required = False
            return
        for field_name in (
            "name_az",
            "category",
            "event_date",
            "start_time_input",
            "end_time_input",
            "age_from",
            "age_to",
            "price_text",
            "description_az",
            "photo",
        ):
            self.fields[field_name].required = True

    def clean_name_az(self):
        return _normalize_whitespace(self.cleaned_data.get("name_az") or "")

    def clean_phone(self):
        value = self.cleaned_data.get("phone") or ""
        if self.draft_save_only and not value:
            return ""
        return _validate_phone(value)

    def clean(self):
        cleaned = super().clean()
        from catalog.services.locations import clean_location_fields
        cleaned = clean_location_fields(self, cleaned)
        related_place = cleaned.get("related_place")
        if related_place:
            if not cleaned.get("address"):
                cleaned["address"] = related_place.address
                self.instance.address = related_place.address
            if not cleaned.get("phone"):
                cleaned["phone"] = related_place.phone1
                self.instance.phone = related_place.phone1
            if cleaned.get("lat") is None:
                cleaned["lat"] = related_place.lat
                self.instance.lat = related_place.lat
            if cleaned.get("lng") is None:
                cleaned["lng"] = related_place.lng
                self.instance.lng = related_place.lng
            if not cleaned.get("district"):
                cleaned["district"] = related_place.district
                self.instance.district = related_place.district
            if not cleaned.get("metro"):
                cleaned["metro"] = related_place.metro
                self.instance.metro = related_place.metro
        if not self.draft_save_only:
            if not cleaned.get("address"):
                self.add_error("address", _("Укажите адрес или выберите связанное место с адресом."))
            if not cleaned.get("phone"):
                self.add_error("phone", _("Укажите телефон / WhatsApp или выберите связанное место с телефоном."))

        event_date = cleaned.get("event_date")
        end_date = cleaned.get("end_date") or event_date
        start_time = cleaned.get("start_time_input")
        end_time = cleaned.get("end_time_input")

        start = None
        end = None
        if event_date and start_time:
            start = datetime.combine(event_date, start_time)
            if timezone.is_naive(start):
                start = timezone.make_aware(start, timezone.get_current_timezone())
        if end_date and end_time:
            end = datetime.combine(end_date, end_time)
            if timezone.is_naive(end):
                end = timezone.make_aware(end, timezone.get_current_timezone())

        cleaned["start_datetime"] = start
        cleaned["end_datetime"] = end
        self.instance.start_datetime = start
        self.instance.end_datetime = end

        if not self.draft_save_only:
            if not event_date:
                self.add_error("event_date", _("Укажите дату мероприятия."))
            if not start_time:
                self.add_error("start_time_input", _("Укажите время начала."))
            if not end_time:
                self.add_error("end_time_input", _("Укажите время окончания."))

        if start and end and start >= end:
            self.add_error("end_time_input", _("Время окончания должно быть позже времени начала."))
        if not self.draft_save_only and start and start < timezone.now():
            self.add_error("event_date", _("Нельзя выбрать прошедшую дату или время начала."))
        if not self.draft_save_only and end and end <= timezone.now():
            self.add_error("end_time_input", _("Нельзя отправить на модерацию уже завершившееся мероприятие."))

        age_from = cleaned.get("age_from")
        age_to = cleaned.get("age_to")
        if age_from is not None and age_to is not None and age_from > age_to:
            self.add_error("age_to", _("Возраст «до» меньше «от»."))

        photo = cleaned.get("photo")
        if photo:
            try:
                _validate_uploaded_image(photo)
            except ValidationError as exc:
                self.add_error("photo", exc)
        return cleaned

    def save(self, commit=True):
        event = super().save(commit=False)
        event.name = event.name_az or event.name_ru or event.name_en or event.name
        if event.related_place:
            if not event.address:
                event.address = event.related_place.address
            if not event.phone:
                event.phone = event.related_place.phone1
            if not event.instagram:
                event.instagram = event.related_place.instagram
        if commit:
            event.save()
            self.save_m2m()
        return event


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


class OwnerSpecialistForm(forms.ModelForm):
    draft_save_only = False
    documents = MultipleFileField(
        label=_("Дипломы и сертификаты"),
        widget=MultipleFileInput(attrs={"class": "field", "multiple": True, "accept": ".pdf,image/*"}),
        required=False,
        help_text=_("Можно загрузить дипломы или сертификаты. Они появятся публично только после проверки."),
    )

    # Extra location fields (not on Specialist model directly)
    location_place = forms.ModelChoiceField(
        label=_("Детский центр (KidsMap)"),
        queryset=Place.objects.filter(deleted_at__isnull=True),
        widget=forms.Select(attrs={"class": "field"}),
        required=False,
        empty_label=_("Не выбрано"),
    )
    location_address = forms.CharField(
        label=_("Собственный адрес/кабинет"),
        max_length=255,
        widget=forms.TextInput(attrs={"class": "field", "placeholder": _("Например: пр. Нефтяников 15")}),
        required=False,
    )
    location_region = forms.ModelChoiceField(
        label=_("Город / Регион"),
        queryset=Region.objects.all(),
        widget=forms.Select(attrs={"class": "field"}),
        required=False,
        empty_label=_("Выберите город"),
    )
    location_district = forms.ModelChoiceField(
        label=_("Район"),
        queryset=District.objects.all(),
        widget=forms.Select(attrs={"class": "field"}),
        required=False,
        empty_label=_("Выберите район"),
    )
    location_metro = forms.ModelChoiceField(
        label=_("Метро"),
        queryset=MetroStation.objects.all(),
        widget=forms.Select(attrs={"class": "field"}),
        required=False,
        empty_label=_("Выберите метро"),
    )

    class Meta:
        model = Specialist
        fields = (
            "name",
            "photo",
            "bio_az",
            "bio_ru",
            "bio_en",
            "specializations",
            "consultation_format",
            "experience_years",
            "age_from",
            "age_to",
            "language_az",
            "language_ru",
            "language_en",
            "price_from",
            "price_to",
            "duration_minutes",
            "phone",
            "whatsapp",
            "instagram",
            "website",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "field", "placeholder": _("Имя и фамилия")}),
            "photo": ImagePreviewFileInput(attrs={"class": "field owner-file-uploader-input", "accept": "image/*"}),
            "bio_az": forms.Textarea(attrs={"class": "field", "rows": 3, "placeholder": _("О себе на азербайджанском")}),
            "bio_ru": forms.Textarea(attrs={"class": "field", "rows": 3, "placeholder": _("О себе на русском")}),
            "bio_en": forms.Textarea(attrs={"class": "field", "rows": 3, "placeholder": _("О себе на английском")}),
            "consultation_format": forms.Select(attrs={"class": "field"}),
            "experience_years": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "5"}),
            "age_from": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "3"}),
            "age_to": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "18"}),
            "price_from": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "30"}),
            "price_to": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "80"}),
            "duration_minutes": forms.TextInput(attrs={"class": "field", "inputmode": "numeric", "pattern": "[0-9]*", "placeholder": "50"}),
            "phone": forms.TextInput(attrs={"class": "field", "placeholder": "+994 50 123 45 67", "inputmode": "tel"}),
            "whatsapp": forms.TextInput(attrs={"class": "field", "placeholder": "+994 50 123 45 67", "inputmode": "tel"}),
            "instagram": forms.TextInput(attrs={"class": "field", "placeholder": "username"}),
            "website": forms.URLInput(attrs={"class": "field", "placeholder": "https://example.com"}),
        }

    def __init__(self, *args, **kwargs):
        self.draft_save_only = bool(kwargs.pop("draft_save_only", False))
        super().__init__(*args, **kwargs)
        self.fields["photo"].help_text = _("JPG, PNG или WEBP. Максимум 2 МБ.")
        self.fields["specializations"].queryset = SpecialistSpecialization.objects.filter(is_active=True).order_by("order", "name_ru")
        self.fields["specializations"].required = False

        # Populate location fields when editing
        if self.instance and self.instance.pk:
            primary_location = self.instance.practice_locations.filter(is_primary=True).first()
            if primary_location:
                self.fields["location_place"].initial = primary_location.place_id
                self.fields["location_address"].initial = primary_location.address
                self.fields["location_region"].initial = primary_location.region_id
                self.fields["location_district"].initial = primary_location.district_id
                self.fields["location_metro"].initial = primary_location.metro_id

        # Draft = all optional; submit = checked in clean().
        if self.draft_save_only:
            for field in self.fields.values():
                field.required = False
        else:
            required = ("name", "consultation_format")
            for field_name, field in self.fields.items():
                field.required = field_name in required

    def clean(self):
        cleaned = super().clean()
        if self.draft_save_only:
            photo = cleaned.get("photo")
            if photo:
                try:
                    _validate_uploaded_image(photo)
                except ValidationError as exc:
                    self.add_error("photo", exc)
            return cleaned

        if not cleaned.get("specializations"):
            self.add_error("specializations", _("Выберите хотя бы одно направление деятельности."))

        if not any((cleaned.get("bio_az"), cleaned.get("bio_ru"), cleaned.get("bio_en"))):
            msg = _("Добавьте описание профиля хотя бы на одном языке.")
            self.add_error("bio_az", msg)
            self.add_error("bio_ru", msg)
            self.add_error("bio_en", msg)

        if not (cleaned.get("phone") or cleaned.get("whatsapp")):
            msg = _("Укажите телефон или WhatsApp для связи.")
            self.add_error("phone", msg)
            self.add_error("whatsapp", msg)

        # Enforce that if format is offline or both, location fields are required and validated
        consultation_format = cleaned.get("consultation_format")
        if consultation_format in [Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH]:
            loc_place = cleaned.get("location_place")
            loc_address = cleaned.get("location_address")
            loc_region = cleaned.get("location_region")
            
            if not loc_place and not loc_address:
                msg = _("Для очного формата укажите детский центр KidsMap или собственный адрес.")
                self.add_error("location_place", msg)
                self.add_error("location_address", msg)
            if not loc_region:
                self.add_error("location_region", _("Выберите город / регион для очной работы."))

        # Enforce at least one language
        lang_az = cleaned.get("language_az")
        lang_ru = cleaned.get("language_ru")
        lang_en = cleaned.get("language_en")
        if not (lang_az or lang_ru or lang_en):
            msg = _("Выберите хотя бы один язык работы.")
            self.add_error("language_az", msg)
            self.add_error("language_ru", msg)
            self.add_error("language_en", msg)

        # Validate ages
        age_from = cleaned.get("age_from")
        age_to = cleaned.get("age_to")
        if age_from is not None and age_to is not None and age_from > age_to:
            self.add_error("age_to", _("Возраст «до» не может быть меньше возраста «от»."))

        # Validate prices
        price_from = cleaned.get("price_from")
        price_to = cleaned.get("price_to")
        if price_from is not None and price_to is not None and price_from > price_to:
            self.add_error("price_to", _("Максимальная стоимость не может быть меньше минимальной."))

        # Validate photo size
        photo = cleaned.get("photo")
        if photo:
            try:
                _validate_uploaded_image(photo)
            except ValidationError as exc:
                self.add_error("photo", exc)

        return cleaned

    def save(self, commit=True):
        return super().save(commit=commit)
