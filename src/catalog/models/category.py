from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language


class Category(models.Model):
    code = models.CharField(_("Код"), max_length=50, primary_key=True)
    name = models.CharField(_("Название"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    icon = models.CharField(_("Иконка"), max_length=50, blank=True, default="", help_text=_("Класс иконки или название"))
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
        if lang == "az":
            return self.name_az or self.name
        if lang == "en":
            return self.name_en or self.name
        return self.name_ru or self.name

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
        if lang == "az":
            return self.name_az or self.name
        if lang == "en":
            return self.name_en or self.name
        return self.name_ru or self.name

    def __str__(self):
        return f"{self.category} -> {self.name_i18n()}"
