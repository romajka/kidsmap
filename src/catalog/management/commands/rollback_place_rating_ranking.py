from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from catalog.services.rating_ranking import clone_and_activate_rating_calibration


class Command(BaseCommand):
    help = "Activate a new calibration version copied from an active or retired version."

    def add_arguments(self, parser):
        parser.add_argument("--to-version", type=int, required=True)
        parser.add_argument("--actor-user-id", type=int, required=True)

    def handle(self, *args, **options):
        actor = get_user_model().objects.filter(pk=options["actor_user_id"]).first()
        if actor is None:
            raise CommandError("Activation actor was not found.")
        try:
            calibration = clone_and_activate_rating_calibration(
                source_version=options["to_version"],
                actor=actor,
            )
        except (PermissionError, TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"rollback_source_version={options['to_version']} activated_version={calibration.version}"
            )
        )
