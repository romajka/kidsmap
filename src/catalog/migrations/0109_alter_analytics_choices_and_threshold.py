import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0108_analytics_measurement")]

    operations = [
        migrations.AlterField(
            model_name="funnelevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("organization_view", "Просмотр организации"), ("place_view", "Просмотр места"),
                    ("activity_view", "Просмотр занятия"), ("favorite_added", "Добавление места в избранное"),
                    ("favorite_removed", "Удаление места из избранного"), ("phone_click", "Клик по телефону"),
                    ("whatsapp_click", "Клик по WhatsApp"), ("website_click", "Клик по сайту"),
                    ("social_click", "Клик по социальной сети"), ("directions_click", "Построение маршрута"),
                    ("catalog_search", "Поиск в каталоге"), ("catalog_filter", "Применение фильтров"),
                    ("place_open", "Открытие карточки"), ("cta_call", "Клик: Позвонить"),
                    ("cta_whatsapp", "Клик: WhatsApp"), ("cta_instagram", "Клик: Instagram"),
                    ("favorite_toggle", "Добавление в избранное"), ("review_submit", "Отправка отзыва"),
                    ("claim_place_start", "Начало заявки на управление"), ("claim_place_submit", "Отправка заявки на управление"),
                    ("add_place_signup_start", "Начало регистрации для добавления места"),
                    ("add_place_signup_complete", "Завершение регистрации для добавления места"),
                    ("ai_referral_visit", "Переход из AI-сервиса"),
                    ("owner_signup_start", "Начало регистрации владельца (архив)"),
                    ("owner_signup_complete", "Завершение регистрации владельца (архив)"),
                ], db_index=True, max_length=32, verbose_name="Событие"
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings", name="public_favorites_minimum",
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name="Минимум добавлений для публичного показа"),
        ),
    ]
