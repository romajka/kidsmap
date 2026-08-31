"""Report team memberships and invitations that are still not tied to a place.

Migration 0093 only converts rows whose owner has exactly one place. Everything
else is listed here so a human can decide, because guessing would hand someone
access to a place they were never given.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from catalog.models import OwnerTeamInvitation, OwnerTeamMembership, Place


class Command(BaseCommand):
    help = "List OwnerTeamMembership/OwnerTeamInvitation rows that have no place assigned."

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Also list inactive memberships and non-pending invitations.",
        )

    def handle(self, *args, **options):
        include_inactive = options["include_inactive"]

        place_counts = dict(
            Place.objects.filter(owner_id__isnull=False)
            .values("owner_id")
            .annotate(place_count=Count("id"))
            .values_list("owner_id", "place_count")
        )

        memberships = OwnerTeamMembership.objects.filter(place__isnull=True).select_related("owner", "member")
        if not include_inactive:
            memberships = memberships.filter(is_active=True)

        invitations = OwnerTeamInvitation.objects.filter(place__isnull=True).select_related("owner")
        if not include_inactive:
            invitations = invitations.filter(status=OwnerTeamInvitation.STATUS_PENDING)

        memberships = list(memberships.order_by("owner_id", "member_id"))
        invitations = list(invitations.order_by("owner_id", "email"))

        if not memberships and not invitations:
            self.stdout.write(self.style.SUCCESS("No legacy team rows without a place. Nothing to resolve."))
            return

        self.stdout.write(self.style.WARNING("These rows grant no access until a place is assigned by hand.\n"))

        if memberships:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Memberships without a place: {len(memberships)}"))
            for membership in memberships:
                self.stdout.write(
                    f"  id={membership.id} owner={self._label(membership.owner)} "
                    f"member={self._label(membership.member)} role={membership.role} "
                    f"active={membership.is_active} reason={self._reason(place_counts, membership.owner_id)}"
                )
            self.stdout.write("")

        if invitations:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Invitations without a place: {len(invitations)}"))
            for invitation in invitations:
                self.stdout.write(
                    f"  id={invitation.id} owner={self._label(invitation.owner)} "
                    f"email={invitation.email} role={invitation.role} "
                    f"status={invitation.status} reason={self._reason(place_counts, invitation.owner_id)}"
                )
            self.stdout.write("")

        self.stdout.write(
            "Resolve each row by setting its place in the admin, or delete it if the access is no longer wanted."
        )

    @staticmethod
    def _label(user) -> str:
        if user is None:
            return "<none>"
        return f"{user.id}:{user.username or user.email or '<unnamed>'}"

    @staticmethod
    def _reason(place_counts: dict[int, int], owner_id: int | None) -> str:
        count = place_counts.get(owner_id, 0)
        if count == 0:
            return "owner has no places"
        if count > 1:
            return f"owner has {count} places (ambiguous)"
        return "single place but assignment collided with an existing row"
