from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0076_place_home_recommendations"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="age_open_ended",
            field=models.BooleanField(
                default=False,
                help_text="Например: 3+; для всех возрастов укажите возраст «от» 0.",
                verbose_name="Без верхней границы возраста",
            ),
        ),
    ]
