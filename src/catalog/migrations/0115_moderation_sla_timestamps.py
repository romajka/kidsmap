from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0114_coordinate_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="submitted_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Отправлено на модерацию"),
        ),
        migrations.AddField(
            model_name="place",
            name="needs_changes_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Возвращено на доработку"),
        ),
        migrations.AddField(
            model_name="place",
            name="moderated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Решение модератора"),
        ),
        migrations.AddField(
            model_name="place",
            name="moderated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="moderated_places", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="placereview",
            name="submitted_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Отправлено на модерацию"),
        ),
        migrations.AddField(
            model_name="placereview",
            name="moderated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Решение модератора"),
        ),
        migrations.AddField(
            model_name="placereview",
            name="moderated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="moderated_place_reviews", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="sitereview",
            name="submitted_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Отправлено на модерацию"),
        ),
        migrations.AddField(
            model_name="sitereview",
            name="moderated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Решение модератора"),
        ),
        migrations.AddField(
            model_name="sitereview",
            name="moderated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="moderated_site_reviews", to=settings.AUTH_USER_MODEL),
        ),
    ]
