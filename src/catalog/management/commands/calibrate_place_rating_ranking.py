from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from catalog.services.rating_ranking import (
    activate_rating_calibration,
    build_place_rating_calibration_proposal,
)


class Command(BaseCommand):
    help = "Calculate a versioned Bayesian Place-rating calibration."

    def add_arguments(self, parser):
        parser.add_argument("--confidence-z", type=float, required=True)
        parser.add_argument("--margin-stars", type=float, required=True)
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true")
        mode.add_argument("--activate", action="store_true")
        parser.add_argument("--actor-user-id", type=int)

    def handle(self, *args, **options):
        try:
            proposal = build_place_rating_calibration_proposal(
                confidence_z=options["confidence_z"],
                margin_stars=options["margin_stars"],
            )
        except (TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        diagnostics = (
            f"version={proposal.version} "
            f"population_review_count={proposal.population_review_count} "
            f"population_place_count={proposal.population_place_count} "
            f"rating_sum={proposal.population_rating_sum} "
            f"rating_sum_squares={proposal.population_rating_sum_squares} "
            f"prior_mean={proposal.prior_mean} "
            f"population_standard_deviation={proposal.population_standard_deviation} "
            f"prior_weight={proposal.prior_weight} "
            f"source_cutoff={proposal.source_cutoff.isoformat()}"
        )
        if options["dry_run"]:
            self.stdout.write(f"dry_run=true {diagnostics}")
            return

        actor_id = options.get("actor_user_id")
        if not actor_id:
            raise CommandError("--actor-user-id is required with --activate.")
        actor = get_user_model().objects.filter(pk=actor_id).first()
        if actor is None:
            raise CommandError("Activation actor was not found.")
        try:
            calibration = activate_rating_calibration(calibration=proposal, actor=actor)
        except (PermissionError, TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"activated=true {diagnostics} id={calibration.pk}"))
