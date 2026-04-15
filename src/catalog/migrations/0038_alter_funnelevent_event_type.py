from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0037_seed_home_hero_site_gallery_images"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funnelevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("catalog_search", "Поиск в каталоге"),
                    ("catalog_filter", "Применение фильтров"),
                    ("place_open", "Открытие карточки"),
                    ("cta_call", "Клик: Позвонить"),
                    ("cta_whatsapp", "Клик: WhatsApp"),
                    ("cta_instagram", "Клик: Instagram"),
                    ("favorite_toggle", "Добавление в избранное"),
                    ("review_submit", "Отправка отзыва"),
                    ("claim_place_start", "Начало заявки на управление"),
                    ("claim_place_submit", "Отправка заявки на управление"),
                    ("owner_signup_start", "Начало регистрации владельца"),
                    ("owner_signup_complete", "Завершение регистрации владельца"),
                ],
                db_index=True,
                max_length=32,
                verbose_name="Событие",
            ),
        ),
    ]
