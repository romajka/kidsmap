"""
Migration: Add soft-delete (deleted_at, deleted_by) and audit fields
(created_at, updated_at, created_by, updated_by) to Category and Subcategory.
Also changes Subcategory.category FK from CASCADE to PROTECT to prevent
accidental data loss when archiving categories.
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0070_fix_regional_demo_place_coordinates"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Category: soft-delete fields ──────────────────────────────────────
        migrations.AddField(
            model_name="category",
            name="deleted_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="Удалена",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="deleted_categories",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто удалил",
            ),
        ),
        # ── Category: audit fields ────────────────────────────────────────────
        migrations.AddField(
            model_name="category",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                null=True,
                verbose_name="Создана",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                null=True,
                verbose_name="Обновлена",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_categories",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто создал",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_categories",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто изменил",
            ),
        ),
        # ── Category: add db_index to is_active ───────────────────────────────
        migrations.AlterField(
            model_name="category",
            name="is_active",
            field=models.BooleanField(
                db_index=True,
                default=True,
                verbose_name="Активна",
            ),
        ),
        # ── Subcategory: change FK from CASCADE to PROTECT ────────────────────
        migrations.AlterField(
            model_name="subcategory",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="subcategories",
                to="catalog.category",
                verbose_name="Категория",
            ),
        ),
        # ── Subcategory: soft-delete fields ──────────────────────────────────
        migrations.AddField(
            model_name="subcategory",
            name="deleted_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="Удалена",
            ),
        ),
        migrations.AddField(
            model_name="subcategory",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="deleted_subcategories",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто удалил",
            ),
        ),
        # ── Subcategory: audit fields ─────────────────────────────────────────
        migrations.AddField(
            model_name="subcategory",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                null=True,
                verbose_name="Создана",
            ),
        ),
        migrations.AddField(
            model_name="subcategory",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                null=True,
                verbose_name="Обновлена",
            ),
        ),
        # ── Subcategory: add db_index to is_active ────────────────────────────
        migrations.AlterField(
            model_name="subcategory",
            name="is_active",
            field=models.BooleanField(
                db_index=True,
                default=True,
                verbose_name="Активна",
            ),
        ),
    ]
