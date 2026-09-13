import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0105_placechangeaudit_volunteer_source"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SuperadminPromotionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Ожидает подтверждения"), ("APPROVED", "Подтверждён"), ("REJECTED", "Отклонён"), ("CANCELLED", "Отменён")], db_index=True, default="PENDING", max_length=16, verbose_name="Статус")),
                ("rejection_note", models.TextField(blank=True, default="", verbose_name="Причина отклонения")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Создан")),
                ("decided_at", models.DateTimeField(blank=True, null=True, verbose_name="Решение принято")),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="decided_superadmin_promotions", to=settings.AUTH_USER_MODEL, verbose_name="Подтвердил или отклонил")),
                ("initiated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="initiated_superadmin_promotions", to=settings.AUTH_USER_MODEL, verbose_name="Инициатор")),
                ("target", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="superadmin_promotion_requests", to=settings.AUTH_USER_MODEL, verbose_name="Кандидат")),
            ],
            options={
                "verbose_name": "Запрос повышения до суперадмина",
                "verbose_name_plural": "Запросы повышения до суперадмина",
                "ordering": ("created_at", "pk"),
            },
        ),
        migrations.CreateModel(
            name="StaffRoleAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor_display", models.CharField(max_length=255, verbose_name="Инициатор на момент действия")),
                ("target_display", models.CharField(max_length=255, verbose_name="Сотрудник на момент действия")),
                ("old_role", models.CharField(blank=True, default="", max_length=32, verbose_name="Старая роль")),
                ("new_role", models.CharField(blank=True, default="", max_length=32, verbose_name="Новая роль")),
                ("action", models.CharField(choices=[("ROLE_CHANGED", "Роль изменена"), ("SUPERADMIN_REQUESTED", "Повышение запрошено"), ("SUPERADMIN_APPROVED", "Повышение подтверждено"), ("SUPERADMIN_REJECTED", "Повышение отклонено"), ("SUPERADMIN_DEMOTION_BLOCKED", "Понижение суперадмина заблокировано"), ("LAST_SUPERADMIN_BLOCKED", "Изменение последнего суперадмина заблокировано")], db_index=True, max_length=40, verbose_name="Действие")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Дата и время")),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="staff_role_actions", to=settings.AUTH_USER_MODEL, verbose_name="Кто изменил")),
                ("promotion_request", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_entries", to="catalog.superadminpromotionrequest", verbose_name="Запрос повышения")),
                ("target", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="staff_role_history", to=settings.AUTH_USER_MODEL, verbose_name="Чья роль")),
            ],
            options={
                "verbose_name": "История роли сотрудника",
                "verbose_name_plural": "История ролей сотрудников",
                "ordering": ("-created_at", "-pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="superadminpromotionrequest",
            constraint=models.UniqueConstraint(condition=models.Q(("status", "PENDING")), fields=("target",), name="catalog_one_pending_superadmin_request_per_target"),
        ),
    ]
