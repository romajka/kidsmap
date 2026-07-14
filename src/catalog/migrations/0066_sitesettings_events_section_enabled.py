from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0065_eventphoto"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="events_section_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Скрывает афишу, временные карточки, ссылки в навигации и owner-формы. Данные и админка мероприятий сохраняются.",
                verbose_name="Показывать раздел «Временные мероприятия»",
            ),
        ),
    ]
