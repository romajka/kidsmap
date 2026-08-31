from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0095_stage4_neutral_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="schedule_mode",
            field=models.CharField(
                choices=[
                    ("regular", "Регулярное по дням недели"),
                    ("by_appointment", "По предварительной записи"),
                    ("variable", "Расписание меняется"),
                    ("events", "По мероприятиям"),
                ],
                default="regular",
                max_length=20,
                verbose_name="Тип расписания",
            ),
        ),
        migrations.AddField(
            model_name="place",
            name="schedule_note_az",
            field=models.TextField(blank=True, default="", verbose_name="Примечание к расписанию (AZ)"),
        ),
        migrations.AddField(
            model_name="place",
            name="schedule_note_en",
            field=models.TextField(blank=True, default="", verbose_name="Примечание к расписанию (EN)"),
        ),
        migrations.AddField(
            model_name="place",
            name="schedule_note_ru",
            field=models.TextField(blank=True, default="", verbose_name="Примечание к расписанию (RU)"),
        ),
    ]
