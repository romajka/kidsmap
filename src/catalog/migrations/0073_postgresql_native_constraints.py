# Generated for the PostgreSQL cutover. This migration intentionally requires
# a database that supports partial unique indexes (PostgreSQL).

from django.db import migrations, models


def require_postgresql(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        raise RuntimeError(
            "Migration 0073 is the PostgreSQL cutover boundary and must not run on MariaDB/MySQL."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0072_subcategory_icon"),
    ]

    operations = [
        migrations.RunPython(require_postgresql, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="placelike",
            name="unique_place_like_per_session",
        ),
        migrations.RemoveConstraint(
            model_name="placereviewreaction",
            name="unique_place_review_reaction_per_session",
        ),
        migrations.RemoveConstraint(
            model_name="sitereviewreaction",
            name="unique_site_review_reaction_per_session",
        ),
        migrations.RemoveConstraint(
            model_name="placeownershiprequest",
            name="unique_pending_ownership_request_per_user_place",
        ),
        migrations.RemoveConstraint(
            model_name="ownerteaminvitation",
            name="unique_pending_team_invitation_per_owner_email",
        ),
        migrations.RemoveField(
            model_name="placelike",
            name="session_key_unique",
        ),
        migrations.RemoveField(
            model_name="placereviewreaction",
            name="session_key_unique",
        ),
        migrations.RemoveField(
            model_name="sitereviewreaction",
            name="session_key_unique",
        ),
        migrations.RemoveField(
            model_name="placeownershiprequest",
            name="pending_constraint_key",
        ),
        migrations.RemoveField(
            model_name="ownerteaminvitation",
            name="pending_email",
        ),
        migrations.AddConstraint(
            model_name="placelike",
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=True) & ~models.Q(session_key=""),
                fields=("place", "session_key"),
                name="unique_place_like_per_session",
            ),
        ),
        migrations.AddConstraint(
            model_name="placereviewreaction",
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=True) & ~models.Q(session_key=""),
                fields=("review", "session_key"),
                name="unique_place_review_reaction_per_session",
            ),
        ),
        migrations.AddConstraint(
            model_name="sitereviewreaction",
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=True) & ~models.Q(session_key=""),
                fields=("review", "session_key"),
                name="unique_site_review_reaction_per_session",
            ),
        ),
        migrations.AddConstraint(
            model_name="placeownershiprequest",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="PENDING"),
                fields=("place", "applicant"),
                name="unique_pending_ownership_request_per_user_place",
            ),
        ),
        migrations.AddConstraint(
            model_name="ownerteaminvitation",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="PENDING"),
                fields=("owner", "email"),
                name="unique_pending_team_invitation_per_owner_email",
            ),
        ),
    ]
