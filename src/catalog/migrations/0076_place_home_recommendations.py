from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0075_normalize_public_slugs"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="home_recommended_order",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Меньшее число показывается раньше. На главной выводятся максимум четыре места.",
                verbose_name="Порядок в рекомендациях",
            ),
        ),
        migrations.AddField(
            model_name="place",
            name="is_home_recommended",
            field=models.BooleanField(
                db_index=True,
                default=False,
                verbose_name="Показывать в рекомендациях на главной",
            ),
        ),
    ]
