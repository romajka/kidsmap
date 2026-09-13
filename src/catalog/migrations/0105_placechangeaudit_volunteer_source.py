from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0104_sitesettings_home_recommendations_limit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="placechangeaudit",
            name="source",
            field=models.CharField(
                choices=[
                    ("OWNER_PANEL", "Управление местами"),
                    ("ADMIN", "Админка"),
                    ("VOLUNTEER", "Волонтёр"),
                    ("SYSTEM", "Система"),
                ],
                db_index=True,
                default="OWNER_PANEL",
                max_length=24,
                verbose_name="Источник",
            ),
        ),
    ]
