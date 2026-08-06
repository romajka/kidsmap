from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class PricingPlan(models.Model):
    PRODUCT_CHOICES = [
        ("admission", _("Входной билет")), ("visit", _("Посещение")),
        ("lesson", _("Занятие")), ("membership", _("Абонемент")),
        ("course", _("Курс")), ("camp", _("Лагерь")),
        ("event", _("Мероприятие")), ("excursion", _("Экскурсия")),
        ("tour", _("Тур")), ("rental", _("Аренда")),
        ("addon", _("Дополнительная услуга")),
        ("registration_fee", _("Регистрационный взнос")),
        ("deposit", _("Депозит")),
    ]
    LESSON_FORMAT_CHOICES = [
        ("open_visit", _("Свободное посещение")),
        ("group", _("Групповой")), ("individual", _("Индивидуальный")),
    ]
    BILLING_MODE_CHOICES = [
        ("one_time", _("Разовая оплата")), ("recurring", _("Регулярная оплата")),
        ("installment", _("Оплата частями")),
    ]
    INTERVAL_CHOICES = [(value, label) for value, label in (
        ("day", _("День")), ("week", _("Неделя")),
        ("month", _("Месяц")), ("year", _("Год")),
    )]
    PRICE_KIND_CHOICES = [
        ("exact", _("Точная цена")), ("free", _("Бесплатно")),
        ("from", _("Цена от")), ("range", _("Диапазон")),
        ("on_request", _("По запросу")),
    ]
    QUANTITY_UNIT_CHOICES = [(value, label) for value, label in (
        ("entry", _("Вход")), ("visit", _("Посещение")), ("lesson", _("Занятие")),
        ("minute", _("Минута")), ("hour", _("Час")), ("day", _("День")),
        ("week", _("Неделя")), ("month", _("Месяц")), ("course", _("Курс")),
        ("event", _("Мероприятие")), ("camp_shift", _("Смена")),
        ("person", _("Человек")), ("family", _("Семья")), ("group", _("Группа")),
    )]
    AUDIENCE_CHOICES = [(value, label) for value, label in (
        ("all", _("Все")), ("child", _("Дети")), ("adult", _("Взрослые")),
        ("family", _("Семья")), ("group", _("Группа")),
    )]
    DAY_TYPE_CHOICES = [(value, label) for value, label in (
        ("any", _("Любой день")), ("weekday", _("Будни")),
        ("weekend", _("Выходные")), ("holiday", _("Праздники")),
    )]
    CHARGE_ROLE_CHOICES = [
        ("primary", _("Основной")), ("addon", _("Дополнительный")),
        ("registration_fee", _("Регистрационный взнос")), ("deposit", _("Депозит")),
    ]

    place = models.ForeignKey("catalog.Place", on_delete=models.CASCADE, related_name="pricing_plan_records")
    product_type = models.CharField(max_length=32, choices=PRODUCT_CHOICES)
    lesson_format = models.CharField(max_length=16, choices=LESSON_FORMAT_CHOICES, blank=True)
    charge_role = models.CharField(max_length=24, choices=CHARGE_ROLE_CHOICES, default="primary")
    billing_mode = models.CharField(max_length=16, choices=BILLING_MODE_CHOICES, default="one_time")
    billing_interval = models.CharField(max_length=8, choices=INTERVAL_CHOICES, blank=True)
    billing_interval_count = models.PositiveSmallIntegerField(null=True, blank=True)
    billing_cycles = models.PositiveSmallIntegerField(null=True, blank=True)
    price_kind = models.CharField(max_length=16, choices=PRICE_KIND_CHOICES, default="exact")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="AZN")
    quantity = models.PositiveSmallIntegerField(null=True, blank=True)
    quantity_unit = models.CharField(max_length=16, choices=QUANTITY_UNIT_CHOICES, blank=True)
    sessions_per_week = models.PositiveSmallIntegerField(null=True, blank=True)
    sessions_per_month = models.PositiveSmallIntegerField(null=True, blank=True)
    is_unlimited = models.BooleanField(default=False)
    validity_interval = models.CharField(max_length=8, choices=INTERVAL_CHOICES, blank=True)
    validity_interval_count = models.PositiveSmallIntegerField(null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    audience_type = models.CharField(max_length=12, choices=AUDIENCE_CHOICES, default="all")
    age_from = models.PositiveSmallIntegerField(null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(null=True, blank=True)
    min_people = models.PositiveSmallIntegerField(null=True, blank=True)
    max_people = models.PositiveSmallIntegerField(null=True, blank=True)
    day_type = models.CharField(max_length=12, choices=DAY_TYPE_CHOICES, default="any")
    title_az = models.CharField(max_length=160, blank=True)
    title_ru = models.CharField(max_length=160, blank=True)
    title_en = models.CharField(max_length=160, blank=True)
    conditions_az = models.TextField(blank=True)
    conditions_ru = models.TextField(blank=True)
    conditions_en = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(fields=("place", "is_active", "charge_role", "currency"), name="pricing_lookup_idx"),
            models.Index(fields=("place", "sort_order", "id"), name="pricing_order_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0) | Q(price__isnull=True), name="pricing_price_nonnegative"),
            models.CheckConstraint(condition=Q(price_min__gte=0) | Q(price_min__isnull=True), name="pricing_min_nonnegative"),
            models.CheckConstraint(condition=Q(price_max__gte=0) | Q(price_max__isnull=True), name="pricing_max_nonnegative"),
            models.CheckConstraint(condition=Q(price_min__lte=models.F("price_max")) | Q(price_min__isnull=True) | Q(price_max__isnull=True), name="pricing_range_order"),
            models.CheckConstraint(
                condition=(
                    Q(price_kind="exact", price__gt=0, price_min__isnull=True, price_max__isnull=True)
                    | Q(price_kind="free", price=0, price_min__isnull=True, price_max__isnull=True)
                    | Q(price_kind="from", price__isnull=True, price_min__gt=0, price_max__isnull=True)
                    | Q(price_kind="range", price__isnull=True, price_min__isnull=False, price_max__isnull=False)
                    | Q(price_kind="on_request", price__isnull=True, price_min__isnull=True, price_max__isnull=True)
                ),
                name="pricing_kind_values",
            ),
            models.CheckConstraint(
                condition=(
                    Q(billing_mode="one_time", billing_interval="", billing_interval_count__isnull=True, billing_cycles__isnull=True)
                    | Q(billing_mode="recurring", billing_interval__in=("day", "week", "month", "year"), billing_interval_count__gt=0, billing_cycles__isnull=True)
                    | Q(billing_mode="installment", billing_interval="", billing_interval_count__isnull=True, billing_cycles__gt=0)
                ),
                name="pricing_billing_values",
            ),
            models.CheckConstraint(
                condition=(Q(quantity__isnull=True, quantity_unit="") | Q(quantity__gt=0) & ~Q(quantity_unit="")),
                name="pricing_quantity_pair",
            ),
            models.CheckConstraint(
                condition=(Q(validity_interval_count__isnull=True, validity_interval="") | Q(validity_interval_count__gt=0) & ~Q(validity_interval="")),
                name="pricing_validity_pair",
            ),
            models.CheckConstraint(condition=Q(age_from__isnull=True) | Q(age_to__isnull=True) | Q(age_from__lte=models.F("age_to")), name="pricing_age_order"),
            models.CheckConstraint(condition=Q(min_people__isnull=True) | Q(max_people__isnull=True) | Q(min_people__lte=models.F("max_people")), name="pricing_people_order"),
            models.CheckConstraint(condition=Q(valid_from__isnull=True) | Q(valid_until__isnull=True) | Q(valid_from__lte=models.F("valid_until")), name="pricing_date_order"),
            models.CheckConstraint(
                condition=(
                    Q(product_type="addon", charge_role="addon")
                    | Q(product_type="registration_fee", charge_role="registration_fee")
                    | Q(product_type="deposit", charge_role="deposit")
                    | Q(charge_role="primary") & ~Q(product_type__in=("addon", "registration_fee", "deposit"))
                ),
                name="pricing_charge_role",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        self.currency = (self.currency or "AZN").strip().upper()

        if self.price_kind == "exact":
            self.price_min = self.price_max = None
            if self.price is None or self.price <= 0:
                errors["price"] = _("Для точной цены укажите сумму больше нуля.")
        elif self.price_kind == "free":
            self.price = Decimal("0")
            self.price_min = self.price_max = None
        elif self.price_kind == "from":
            self.price = self.price_max = None
            if self.price_min is None or self.price_min <= 0:
                errors["price_min"] = _("Для цены «от» укажите сумму больше нуля.")
        elif self.price_kind == "range":
            self.price = None
            if self.price_min is None:
                errors["price_min"] = _("Укажите нижнюю границу цены.")
            if self.price_max is None:
                errors["price_max"] = _("Укажите верхнюю границу цены.")
            if self.price_min is not None and self.price_max is not None and self.price_min > self.price_max:
                errors["price_max"] = _("Верхняя граница не может быть меньше нижней.")
        elif self.price_kind == "on_request":
            self.price = self.price_min = self.price_max = None

        if self.billing_mode == "recurring":
            if not self.billing_interval:
                errors["billing_interval"] = _("Для регулярной оплаты укажите период.")
            if not self.billing_interval_count:
                errors["billing_interval_count"] = _("Укажите количество периодов больше нуля.")
            self.billing_cycles = None
        elif self.billing_mode == "installment":
            if not self.billing_cycles:
                errors["billing_cycles"] = _("Для оплаты частями укажите количество платежей.")
            self.billing_interval = ""
            self.billing_interval_count = None
        else:
            self.billing_interval = ""
            self.billing_interval_count = None
            self.billing_cycles = None

        if bool(self.quantity) != bool(self.quantity_unit):
            if self.quantity and not self.quantity_unit:
                default_units = {
                    "admission": "entry", "visit": "visit", "lesson": "lesson",
                    "membership": "lesson", "course": "course", "camp": "camp_shift",
                    "event": "event", "excursion": "event", "tour": "event", "rental": "hour",
                }
                self.quantity_unit = default_units.get(self.product_type, "entry" if self.product_type == "admission" else "lesson")
            else:
                errors["quantity"] = _("Количество и единица должны быть указаны вместе.")
        if self.validity_interval_count and not self.validity_interval:
            errors["validity_interval"] = _("Укажите единицу срока действия.")
        if self.validity_interval and not self.validity_interval_count:
            errors["validity_interval_count"] = _("Укажите срок действия больше нуля.")
        if self.age_from is not None and self.age_to is not None and self.age_from > self.age_to:
            errors["age_to"] = _("Возраст «до» не может быть меньше возраста «от».")
        if self.min_people is not None and self.max_people is not None and self.min_people > self.max_people:
            errors["max_people"] = _("Максимум людей не может быть меньше минимума.")
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            errors["valid_until"] = _("Дата окончания не может быть раньше даты начала.")
        for field_name in (
            "billing_interval_count", "billing_cycles", "quantity", "sessions_per_week",
            "sessions_per_month", "validity_interval_count", "min_people", "max_people",
        ):
            value = getattr(self, field_name)
            if value is not None and value <= 0:
                errors[field_name] = _("Значение должно быть больше нуля.")

        forced_roles = {"addon": "addon", "registration_fee": "registration_fee", "deposit": "deposit"}
        expected_role = forced_roles.get(self.product_type)
        if expected_role and self.charge_role != expected_role:
            errors["charge_role"] = _("Роль платежа не соответствует типу тарифа.")
        if self.charge_role != "primary" and self.product_type not in forced_roles:
            errors["product_type"] = _("Для дополнительного платежа выберите соответствующий тип продукта.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def title_i18n(self, language="az"):
        language = (language or "az").split("-")[0]
        return getattr(self, f"title_{language}", "") or self.title_az or self.title_ru or self.title_en or self.get_product_type_display()

    def conditions_i18n(self, language="az"):
        language = (language or "az").split("-")[0]
        return getattr(self, f"conditions_{language}", "") or self.conditions_az or self.conditions_ru or self.conditions_en


@receiver(post_save, sender=PricingPlan)
@receiver(post_delete, sender=PricingPlan)
def _sync_pricing_plan_legacy_fields(sender, instance, **kwargs):
    if getattr(instance, "_skip_legacy_sync", False):
        return
    from catalog.services.pricing_plans import sync_legacy_price_fields
    sync_legacy_price_fields(instance.place_id)
