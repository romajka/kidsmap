from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0050_migrate_to_hierarchical_districts"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlaceScheduleDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weekday", models.CharField(choices=[("mon", "Понедельник"), ("tue", "Вторник"), ("wed", "Среда"), ("thu", "Четверг"), ("fri", "Пятница"), ("sat", "Суббота"), ("sun", "Воскресенье")], max_length=3, verbose_name="День недели")),
                ("is_closed", models.BooleanField(default=True, verbose_name="Закрыто")),
                ("is_24_hours", models.BooleanField(default=False, verbose_name="24 часа")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")),
                ("place", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="schedule_days", to="catalog.place", verbose_name="Место")),
            ],
            options={
                "verbose_name": "День расписания",
                "verbose_name_plural": "Дни расписания",
                "ordering": ("order", "id"),
            },
        ),
        migrations.CreateModel(
            name="PlaceScheduleInterval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_time", models.TimeField(verbose_name="Начало")),
                ("end_time", models.TimeField(verbose_name="Окончание")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")),
                ("schedule_day", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="intervals", to="catalog.placescheduleday", verbose_name="День расписания")),
            ],
            options={
                "verbose_name": "Интервал расписания",
                "verbose_name_plural": "Интервалы расписания",
                "ordering": ("order", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="placescheduleday",
            constraint=models.UniqueConstraint(fields=("place", "weekday"), name="unique_place_schedule_weekday"),
        ),
    ]
