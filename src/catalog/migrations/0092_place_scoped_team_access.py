# Generated manually for the first stage of user-model refactoring.

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0091_place_custom_price_badge_az_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerteammembership",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="team_memberships",
                to="catalog.place",
                verbose_name="Карточка",
            ),
        ),
        migrations.AddField(
            model_name="ownerteaminvitation",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="team_invitations",
                to="catalog.place",
                verbose_name="Карточка",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="ownerteammembership",
            name="unique_owner_team_member",
        ),
        migrations.RemoveConstraint(
            model_name="ownerteaminvitation",
            name="unique_pending_team_invitation_per_owner_email",
        ),
        migrations.AddConstraint(
            model_name="ownerteammembership",
            constraint=models.UniqueConstraint(
                condition=models.Q(("place__isnull", False)),
                fields=("place", "member"),
                name="unique_place_team_member",
            ),
        ),
        migrations.AddConstraint(
            model_name="ownerteaminvitation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("place__isnull", False), ("status", "PENDING")),
                fields=("place", "email"),
                name="unique_pending_team_invitation_per_place_email",
            ),
        ),
        migrations.AlterField(
            model_name="ownerteaminvitation",
            name="role",
            field=models.CharField(
                choices=[("MANAGER", "Менеджер"), ("MODERATOR", "Модератор"), ("EDITOR", "Редактор")],
                db_index=True,
                default="EDITOR",
                max_length=16,
                verbose_name="Роль в команде",
            ),
        ),
        migrations.AlterField(
            model_name="ownerteammembership",
            name="role",
            field=models.CharField(
                choices=[("MANAGER", "Менеджер"), ("MODERATOR", "Модератор"), ("EDITOR", "Редактор")],
                db_index=True,
                default="EDITOR",
                max_length=16,
                verbose_name="Роль в команде",
            ),
        ),
    ]
