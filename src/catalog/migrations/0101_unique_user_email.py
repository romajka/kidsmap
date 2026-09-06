"""Protect every User writer, including Google/signup/admin and concurrent requests.

auth.User belongs to Django, so this reversible database-only index intentionally
does not change its model state. Empty emails used by legacy/admin users are allowed.
"""
from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower, Trim


def add_unique_email_index(apps, schema_editor):
    User = apps.get_model("auth", "User")
    duplicates = (
        User.objects.using(schema_editor.connection.alias)
        .annotate(normalized_email=Lower(Trim("email")))
        .exclude(normalized_email="")
        .values("normalized_email").annotate(total=Count("pk")).filter(total__gt=1)
    )
    if duplicates.exists():
        raise RuntimeError(
            "Duplicate normalized User emails exist. Resolve account ownership before "
            "applying catalog.0101; no users were merged or removed. See docs/GOOGLE_OAUTH.md."
        )
    if schema_editor.connection.vendor not in {"postgresql", "sqlite"}:
        raise RuntimeError("Google auth requires PostgreSQL (production) or SQLite (development).")
    schema_editor.execute(
        'CREATE UNIQUE INDEX kidsmap_user_email_ci_unique ON auth_user '
        '(LOWER(TRIM(email))) WHERE TRIM(email) <> \'\''
    )


def remove_unique_email_index(apps, schema_editor):
    schema_editor.execute("DROP INDEX kidsmap_user_email_ci_unique")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0100_place_price_mode"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(add_unique_email_index, remove_unique_email_index)]
