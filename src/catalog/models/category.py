from django.contrib.auth.models import User
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.utils import timezone
import os


CATEGORY_COLOR_PRESETS = {
    "ALL": {"bg": "#DDF3E5", "text": "#0F8A43"},
    "SPRT": {"bg": "#E4F0FF", "text": "#1473E6"},
    "ART": {"bg": "#F3E8FF", "text": "#8B5CF6"},
    "MUS": {"bg": "#F8E3FF", "text": "#C026D3"},
    "EDU": {"bg": "#E6ECFF", "text": "#4F46E5"},
    "TECH": {"bg": "#EEE7FF", "text": "#7C3AED"},
    "FUN": {"bg": "#FFE8D9", "text": "#DD6B20"},
    "PARK": {"bg": "#DFF6E8", "text": "#198754"},
    "BEACH": {"bg": "#CCFBF1", "text": "#0F766E"},
    "WATERPARK": {"bg": "#DBEAFE", "text": "#2563EB"},
    "ZOO": {"bg": "#ECFCCB", "text": "#4D7C0F"},
}

NEUTRAL_BG_VALUES = {"", "#fff", "#ffffff", "#f3f4f6", "#fcfcfc", "#f9fafb"}
NEUTRAL_TEXT_VALUES = {"", "#000", "#000000", "#111827", "#1f2933", "#6b7280", "#9ca3af"}


def _normalize_hex(value: str) -> str:
    return str(value or "").strip().lower()


class ActiveCategoryManager(models.Manager):
    """Returns only active, non-deleted categories (for public-facing queries)."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, deleted_at__isnull=True)


class Category(models.Model):
    code = models.CharField(_("Код"), max_length=50, primary_key=True)
    name = models.CharField(_("Название"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    icon = models.CharField(_("Иконка"), max_length=255, blank=True, default="", help_text=_("Класс иконки или название"))
    color_bg = models.CharField(_("Цвет фона (HEX)"), max_length=20, blank=True, default="#F3F4F6", help_text=_("Например: #E8F5EE"))
    color_text = models.CharField(_("Цвет иконки (HEX)"), max_length=20, blank=True, default="#6B7280", help_text=_("Например: #0C7A47"))
    is_active = models.BooleanField(_("Активна"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    # Soft-delete fields
    deleted_at = models.DateTimeField(_("Удалена"), null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="deleted_categories", verbose_name=_("Кто удалил"),
    )

    # Audit fields
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True, null=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_categories", verbose_name=_("Кто создал"),
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="updated_categories", verbose_name=_("Кто изменил"),
    )

    objects = models.Manager()  # default manager (all records)
    active = ActiveCategoryManager()  # public-facing: only active + non-deleted

    class Meta:
        ordering = ("order", "name_ru")
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")

    def name_i18n(self, lang=None):
        if not lang:
            lang = get_language() or "ru"
        lang = lang.split("-")[0]
        if lang == "az":
            val = self.name_az or self.name
        elif lang == "en":
            val = self.name_en or self.name
        else:
            val = self.name_ru or self.name
        return val

    @property
    def icon_name(self):
        return (self.icon or "").strip()

    @property
    def icon_file_url(self):
        icon_name = self.icon_name
        if not icon_name:
            return ""

        ext = os.path.splitext(icon_name)[1].lower()
        if ext not in {".svg", ".png", ".jpg", ".jpeg", ".webp"}:
            return ""

        if icon_name.startswith(("http://", "https://", "/")):
            return icon_name
        return static(icon_name)

    @property
    def icon_is_svg(self):
        return self.icon_file_url.lower().endswith(".svg")

    @property
    def icon_is_font_class(self):
        return bool(self.icon_name and not self.icon_file_url)

    @property
    def color_preset(self):
        return CATEGORY_COLOR_PRESETS.get((self.code or "").strip().upper(), {})

    @property
    def resolved_color_bg(self):
        raw = (self.color_bg or "").strip()
        preset = self.color_preset.get("bg", "#F3F4F6")
        return preset if _normalize_hex(raw) in NEUTRAL_BG_VALUES else raw

    @property
    def resolved_color_text(self):
        raw = (self.color_text or "").strip()
        preset = self.color_preset.get("text", "#6B7280")
        return preset if _normalize_hex(raw) in NEUTRAL_TEXT_VALUES else raw

    def archive(self, user=None):
        """Soft-delete: mark as deleted without removing from DB."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_active", "deleted_at", "deleted_by", "updated_at"])

    def restore(self, user=None):
        """Restore a soft-deleted category."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.updated_by = user
        self.save(update_fields=["is_active", "deleted_at", "deleted_by", "updated_by", "updated_at"])

    def __str__(self):
        return self.name_i18n()


class ActiveSubcategoryManager(models.Manager):
    """Returns only active, non-deleted subcategories."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, deleted_at__isnull=True)


class Subcategory(models.Model):
    # PROTECT instead of CASCADE: prevents accidental deletion of subcategories
    # when a category is deleted. Category must be archived (soft-deleted) instead.
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="subcategories", verbose_name=_("Категория")
    )
    code = models.CharField(_("Код"), max_length=50, unique=True)
    name = models.CharField(_("Название"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    icon = models.CharField(_("Иконка"), max_length=255, blank=True, default="", help_text=_("Путь к загруженной иконке"))
    is_active = models.BooleanField(_("Активна"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    # Soft-delete fields
    deleted_at = models.DateTimeField(_("Удалена"), null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="deleted_subcategories", verbose_name=_("Кто удалил"),
    )

    # Audit fields
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True, null=True)

    objects = models.Manager()  # default manager (all records)
    active = ActiveSubcategoryManager()  # public-facing: only active + non-deleted

    class Meta:
        ordering = ("category__order", "order", "name_ru")
        verbose_name = _("Подкатегория")
        verbose_name_plural = _("Подкатегории")

    def archive(self, user=None):
        """Soft-delete: mark as deleted without removing from DB."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_active", "deleted_at", "deleted_by", "updated_at"])

    def restore(self, user=None):
        """Restore a soft-deleted subcategory."""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_active", "deleted_at", "deleted_by", "updated_at"])

    def name_i18n(self, lang=None):
        if not lang:
            lang = get_language() or "ru"
        lang = lang.split("-")[0]
        if lang == "az":
            val = self.name_az or self.name
        elif lang == "en":
            val = self.name_en or self.name
        else:
            val = self.name_ru or self.name
        return val

    @property
    def icon_file_url(self):
        icon_name = (self.icon or "").strip()
        if not icon_name:
            return ""
        if icon_name.startswith(("http://", "https://", "/")):
            return icon_name
        return static(icon_name)

    def __str__(self):
        return f"{self.category} -> {self.name_i18n()}"
