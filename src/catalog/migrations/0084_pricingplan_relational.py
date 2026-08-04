import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0083_alter_sitegalleryimage_category")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(model_name="place", old_name="pricing_plans", new_name="pricing_plans_legacy"),
                migrations.AlterField(model_name="place", name="pricing_plans_legacy", field=models.JSONField(blank=True, db_column="pricing_plans", default=list, verbose_name="Старые тарифы JSON")),
            ],
        ),
        migrations.AlterField(model_name="place", name="price_from", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Цена от")),
        migrations.AlterField(model_name="place", name="price_to", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Цена до")),
        migrations.AlterField(model_name="place", name="price_per_lesson", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Цена за 1 урок")),
        migrations.AlterField(model_name="place", name="price_per_month", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Цена за месяц")),
        migrations.AlterField(model_name="place", name="price_per_8_lessons", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Цена за 8 уроков")),
        migrations.CreateModel(
            name="PricingPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_type", models.CharField(choices=[("admission", "Входной билет"), ("visit", "Посещение"), ("lesson", "Занятие"), ("membership", "Абонемент"), ("course", "Курс"), ("camp", "Лагерь"), ("event", "Мероприятие"), ("excursion", "Экскурсия"), ("tour", "Тур"), ("rental", "Аренда"), ("addon", "Дополнительная услуга"), ("registration_fee", "Регистрационный взнос"), ("deposit", "Депозит")], max_length=32)),
                ("lesson_format", models.CharField(blank=True, choices=[("open_visit", "Свободное посещение"), ("group", "Групповой"), ("individual", "Индивидуальный")], max_length=16)),
                ("charge_role", models.CharField(choices=[("primary", "Основной"), ("addon", "Дополнительный"), ("registration_fee", "Регистрационный взнос"), ("deposit", "Депозит")], default="primary", max_length=24)),
                ("billing_mode", models.CharField(choices=[("one_time", "Разовая оплата"), ("recurring", "Регулярная оплата"), ("installment", "Оплата частями")], default="one_time", max_length=16)),
                ("billing_interval", models.CharField(blank=True, choices=[("day", "День"), ("week", "Неделя"), ("month", "Месяц"), ("year", "Год")], max_length=8)),
                ("billing_interval_count", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("billing_cycles", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("price_kind", models.CharField(choices=[("exact", "Точная цена"), ("free", "Бесплатно"), ("from", "Цена от"), ("range", "Диапазон"), ("on_request", "По запросу")], default="exact", max_length=16)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("price_min", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("price_max", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("currency", models.CharField(default="AZN", max_length=3)),
                ("quantity", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("quantity_unit", models.CharField(blank=True, choices=[("entry", "Вход"), ("visit", "Посещение"), ("lesson", "Занятие"), ("minute", "Минута"), ("hour", "Час"), ("day", "День"), ("week", "Неделя"), ("month", "Месяц"), ("course", "Курс"), ("event", "Мероприятие"), ("camp_shift", "Смена"), ("person", "Человек"), ("family", "Семья"), ("group", "Группа")], max_length=16)),
                ("sessions_per_week", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("sessions_per_month", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("is_unlimited", models.BooleanField(default=False)),
                ("validity_interval", models.CharField(blank=True, choices=[("day", "День"), ("week", "Неделя"), ("month", "Месяц"), ("year", "Год")], max_length=8)),
                ("validity_interval_count", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("valid_from", models.DateField(blank=True, null=True)), ("valid_until", models.DateField(blank=True, null=True)),
                ("audience_type", models.CharField(choices=[("all", "Все"), ("child", "Дети"), ("adult", "Взрослые"), ("family", "Семья"), ("group", "Группа")], default="all", max_length=12)),
                ("age_from", models.PositiveSmallIntegerField(blank=True, null=True)), ("age_to", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("min_people", models.PositiveSmallIntegerField(blank=True, null=True)), ("max_people", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("day_type", models.CharField(choices=[("any", "Любой день"), ("weekday", "Будни"), ("weekend", "Выходные"), ("holiday", "Праздники")], default="any", max_length=12)),
                ("title_az", models.CharField(blank=True, max_length=160)), ("title_ru", models.CharField(blank=True, max_length=160)), ("title_en", models.CharField(blank=True, max_length=160)),
                ("conditions_az", models.TextField(blank=True)), ("conditions_ru", models.TextField(blank=True)), ("conditions_en", models.TextField(blank=True)),
                ("is_required", models.BooleanField(default=False)), ("is_active", models.BooleanField(default=True)), ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("verified_at", models.DateTimeField(blank=True, null=True)), ("source_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("place", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pricing_plan_records", to="catalog.place")),
            ],
            options={"ordering": ("sort_order", "id")},
        ),
        migrations.AddIndex(model_name="pricingplan", index=models.Index(fields=["place", "is_active", "charge_role", "currency"], name="pricing_lookup_idx")),
        migrations.AddIndex(model_name="pricingplan", index=models.Index(fields=["place", "sort_order", "id"], name="pricing_order_idx")),
        migrations.AddConstraint(model_name="pricingplan", constraint=models.CheckConstraint(condition=models.Q(("price__gte", 0), ("price__isnull", True), _connector="OR"), name="pricing_price_nonnegative")),
        migrations.AddConstraint(model_name="pricingplan", constraint=models.CheckConstraint(condition=models.Q(("price_min__gte", 0), ("price_min__isnull", True), _connector="OR"), name="pricing_min_nonnegative")),
        migrations.AddConstraint(model_name="pricingplan", constraint=models.CheckConstraint(condition=models.Q(("price_max__gte", 0), ("price_max__isnull", True), _connector="OR"), name="pricing_max_nonnegative")),
        migrations.AddConstraint(model_name="pricingplan", constraint=models.CheckConstraint(condition=models.Q(("price_min__lte", models.F("price_max")), ("price_min__isnull", True), ("price_max__isnull", True), _connector="OR"), name="pricing_range_order")),
    ]
