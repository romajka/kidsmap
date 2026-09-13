import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def remove_anonymous_favorites(apps, schema_editor):
    PlaceLike = apps.get_model("catalog", "PlaceLike")
    Place = apps.get_model("catalog", "Place")
    PlaceLike.objects.filter(user__isnull=True).delete()
    Place.objects.all().update(likes_count=0)
    for row in (
        PlaceLike.objects.filter(user__is_active=True)
        .values("place_id")
        .annotate(total=models.Count("user_id", distinct=True))
    ):
        Place.objects.filter(pk=row["place_id"]).update(likes_count=row["total"])


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0107_account_deletion_retention"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name="sitesettings", name="public_favorites_count_enabled", field=models.BooleanField(default=False, verbose_name="Показывать публичное число добавлений в избранное")),
        migrations.AddField(model_name="sitesettings", name="public_favorites_minimum", field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Минимум добавлений для публичного показа")),
        migrations.AddField(model_name="funnelevent", name="schema_version", field=models.PositiveSmallIntegerField(db_index=True, default=1)),
        migrations.AddField(model_name="funnelevent", name="subject_type", field=models.CharField(blank=True, db_index=True, default="", max_length=24)),
        migrations.AddField(model_name="funnelevent", name="subject_id", field=models.PositiveBigIntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name="funnelevent", name="occurred_at", field=models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
        migrations.AddField(model_name="funnelevent", name="visitor_key_hash", field=models.CharField(blank=True, db_index=True, default="", max_length=80)),
        migrations.AddField(model_name="funnelevent", name="session_key_hash", field=models.CharField(blank=True, db_index=True, default="", max_length=80)),
        migrations.AddField(model_name="funnelevent", name="source", field=models.CharField(blank=True, db_index=True, default="", max_length=40)),
        migrations.AddField(model_name="funnelevent", name="page_type", field=models.CharField(blank=True, db_index=True, default="", max_length=40)),
        migrations.AddField(model_name="funnelevent", name="language", field=models.CharField(blank=True, db_index=True, default="", max_length=8)),
        migrations.AddField(model_name="funnelevent", name="device_class", field=models.CharField(blank=True, db_index=True, default="", max_length=16)),
        migrations.AddField(model_name="funnelevent", name="referrer_domain", field=models.CharField(blank=True, db_index=True, default="", max_length=180)),
        migrations.AddField(model_name="funnelevent", name="campaign", field=models.CharField(blank=True, db_index=True, default="", max_length=80)),
        migrations.AddIndex(model_name="funnelevent", index=models.Index(fields=["subject_type", "subject_id", "occurred_at", "event_type"], name="funnel_subject_time_idx")),
        migrations.AddIndex(model_name="funnelevent", index=models.Index(fields=["event_type", "occurred_at"], name="funnel_event_time_idx")),
        migrations.AddConstraint(model_name="funnelevent", constraint=models.CheckConstraint(condition=models.Q(("schema_version", 1), models.Q(("subject_type__gt", ""), ("subject_id__isnull", False)), _connector="OR"), name="funnel_v2_requires_subject")),
        migrations.CreateModel(
            name="AnalyticsActorExclusion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason_code", models.CharField(choices=[("staff_test", "Тестовый или служебный аккаунт"), ("suspected_abuse", "Подозрение на накрутку"), ("privacy", "Исключение по приватности")], max_length=32)),
                ("actor_key_hash", models.CharField(blank=True, default="", max_length=80)),
                ("starts_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("ends_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_analytics_exclusions", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analytics_exclusions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Исключение из аналитики", "verbose_name_plural": "Исключения из аналитики"},
        ),
        migrations.AddIndex(model_name="analyticsactorexclusion", index=models.Index(fields=["user", "starts_at", "ends_at"], name="analytics_excl_active_idx")),
        migrations.RunPython(remove_anonymous_favorites, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name="placelike", name="unique_place_like_per_session"),
        migrations.AlterField(model_name="placelike", name="user", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="place_likes", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
    ]
