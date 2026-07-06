from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
import os


class Category(models.Model):
    code = models.CharField(_("Код"), max_length=50, primary_key=True)
    name = models.CharField(_("Название"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    icon = models.CharField(_("Иконка"), max_length=255, blank=True, default="", help_text=_("Класс иконки или название"))
    color_bg = models.CharField(_("Цвет фона (HEX)"), max_length=20, blank=True, default="#F3F4F6", help_text=_("Например: #E8F5EE"))
    color_text = models.CharField(_("Цвет иконки (HEX)"), max_length=20, blank=True, default="#6B7280", help_text=_("Например: #0C7A47"))
    is_active = models.BooleanField(_("Активна"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("name_ru",)
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")

    def name_i18n(self, lang=None):
        if not lang:
            lang = get_language() or "ru"
        lang = lang.split("-")[0]
        from django.utils.translation import gettext as _
        if lang == "az":
            val = self.name_az or self.name
        elif lang == "en":
            val = self.name_en or self.name
        else:
            val = self.name_ru or self.name
        return _(val)

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

    def __str__(self):
        return self.name_i18n()


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories", verbose_name=_("Категория"))
    code = models.CharField(_("Код"), max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(_("Название"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    is_active = models.BooleanField(_("Активна"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("category", "name_ru")
        verbose_name = _("Подкатегория")
        verbose_name_plural = _("Подкатегории")

    def name_i18n(self, lang=None):
        if not lang:
            lang = get_language() or "ru"
        lang = lang.split("-")[0]
        from django.utils.translation import gettext as _
        if lang == "az":
            val = self.name_az or self.name
        elif lang == "en":
            val = self.name_en or self.name
        else:
            val = self.name_ru or self.name
        return _(val)

    def __str__(self):
        return f"{self.category} -> {self.name_i18n()}"
