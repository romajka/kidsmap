from django.db import models

class Place(models.Model):
    CATEGORY_CHOICES = [
        ("SPRT", "Спорт"),
        ("ART", "Творчество"),
        ("MUS", "Музыка и сцена"),
        ("EDU", "Образование"),
        ("TECH", "Технологии"),
        ("FUN", "Развлечения и досуг"),
        ("CAMP", "Лагеря"),
    ]

    name = models.CharField("Название", max_length=255)
    category = models.CharField("Категория", max_length=10, choices=CATEGORY_CHOICES)
    subcategory = models.CharField("Подкатегория", max_length=255, blank=True)

    age_from = models.PositiveSmallIntegerField("Возраст от", null=True, blank=True)
    age_to = models.PositiveSmallIntegerField("Возраст до", null=True, blank=True)

    district = models.CharField("Район", max_length=100, blank=True)
    metro = models.CharField("Метро", max_length=100, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)

    phone1 = models.CharField("Телефон 1", max_length=50, blank=True)
    instagram = models.CharField("Instagram", max_length=255, blank=True)

    price_from = models.IntegerField("Цена от", null=True, blank=True)
    price_to = models.IntegerField("Цена до", null=True, blank=True)

    is_verified = models.BooleanField("Проверено", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name