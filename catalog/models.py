from django.db import models
from django.utils.translation import gettext_lazy as _


class Place(models.Model):
    CATEGORY_CHOICES = [
        ("SPRT", _("Спорт")),
        ("ART", _("Творчество")),
        ("MUS", _("Музыка и сцена")),
        ("EDU", _("Образование")),
        ("TECH", _("Технологии")),
        ("FUN", _("Развлечения и досуг")),
        ("CAMP", _("Лагеря")),
    ]

    name = models.CharField(_("Название"), max_length=255)
    category = models.CharField(_("Категория"), max_length=10, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(_("Подкатегория"), max_length=255, blank=True)

    age_from = models.PositiveSmallIntegerField(_("Возраст от"), null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(_("Возраст до"), null=True, blank=True)

    district = models.CharField(_("Район"), max_length=100, blank=True)
    metro = models.CharField(_("Метро"), max_length=100, blank=True)
    address = models.CharField(_("Адрес"), max_length=255, blank=True)

    phone1 = models.CharField(_("Телефон 1"), max_length=50, blank=True)
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)

    price_from = models.IntegerField(_("Цена от"), null=True, blank=True)
    price_to = models.IntegerField(_("Цена до"), null=True, blank=True)

    is_verified = models.BooleanField(_("Проверено"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
