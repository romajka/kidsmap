"""Backfill place-scoped team access for rows created before migration 0092.

Before 0092 a membership or invitation was attached to an owner account and
implicitly covered every place that owner had. A row can therefore only be
converted without guessing when the owner has exactly one place: in that case
the old "all places of this owner" scope and the new "this place" scope are the
same set. Owners with several places are ambiguous and are deliberately left
untouched — a NULL place grants no access at all, so leaving them is the safe
outcome. Use `manage.py report_legacy_team_access` to list what stayed behind.
"""

from django.db import migrations
from django.db.models import Count


def _single_place_by_owner(Place) -> dict[int, int]:
    """Map owner_id -> place_id for owners that have exactly one place.

    Soft-deleted places are counted too: the legacy membership covered them as
    well, so ignoring them could silently narrow an owner's scope.
    """
    owner_ids = (
        Place.objects.filter(owner_id__isnull=False)
        .values("owner_id")
        .annotate(place_count=Count("id"))
        .filter(place_count=1)
        .values_list("owner_id", flat=True)
    )
    return {
        place.owner_id: place.id
        for place in Place.objects.filter(owner_id__in=list(owner_ids)).only("id", "owner_id")
    }


def backfill_place_scope(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    OwnerTeamMembership = apps.get_model("catalog", "OwnerTeamMembership")
    OwnerTeamInvitation = apps.get_model("catalog", "OwnerTeamInvitation")

    single_place_by_owner = _single_place_by_owner(Place)
    if not single_place_by_owner:
        return

    for membership in OwnerTeamMembership.objects.filter(place_id__isnull=True).iterator():
        place_id = single_place_by_owner.get(membership.owner_id)
        if place_id is None:
            continue
        # unique_place_team_member would reject a duplicate; an existing
        # place-scoped row already expresses this access.
        clashes = (
            OwnerTeamMembership.objects.filter(place_id=place_id, member_id=membership.member_id)
            .exclude(pk=membership.pk)
            .exists()
        )
        if clashes:
            continue
        membership.place_id = place_id
        membership.save(update_fields=["place"])

    for invitation in OwnerTeamInvitation.objects.filter(place_id__isnull=True).iterator():
        place_id = single_place_by_owner.get(invitation.owner_id)
        if place_id is None:
            continue
        if invitation.status == "PENDING":
            # unique_pending_team_invitation_per_place_email covers pending rows only.
            clashes = (
                OwnerTeamInvitation.objects.filter(
                    place_id=place_id,
                    email=invitation.email,
                    status="PENDING",
                )
                .exclude(pk=invitation.pk)
                .exists()
            )
            if clashes:
                continue
        invitation.place_id = place_id
        invitation.save(update_fields=["place"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0092_place_scoped_team_access"),
    ]

    operations = [
        # Reverse is a no-op: the rows this sets are indistinguishable afterwards
        # from rows that were already place-scoped, so unsetting them would
        # destroy real access data. Rolling back 0092 drops the column anyway.
        migrations.RunPython(backfill_place_scope, migrations.RunPython.noop),
    ]
