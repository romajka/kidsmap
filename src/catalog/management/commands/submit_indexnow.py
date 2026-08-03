from django.core.management.base import BaseCommand, CommandError

from catalog.models import CatalogContentSettings, Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.indexnow import (
    MAX_URLS_PER_REQUEST,
    indexnow_enabled,
    place_canonical_urls,
    seo_landing_canonical_urls,
    submit_indexnow_urls,
)
from catalog.services.seo_landing_visibility import build_seo_landing_visibility


class Command(BaseCommand):
    help = "Submit current public place and indexable SEO landing URLs to IndexNow."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the number of eligible URLs without sending a request.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignore the per-URL cooldown. Use only for an intentional re-submit.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Submit at most this many URLs (0 means all current URLs).",
        )

    def handle(self, *args, **options):
        if not indexnow_enabled():
            raise CommandError("INDEXNOW_KEY is not configured.")
        if options["limit"] < 0:
            raise CommandError("--limit cannot be negative.")

        urls = self._current_urls()
        if options["limit"]:
            urls = urls[: options["limit"]]

        self.stdout.write(f"Eligible canonical URLs: {len(urls)}")
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete; nothing was sent."))
            return

        submitted = 0
        accepted_batches = 0
        for offset in range(0, len(urls), MAX_URLS_PER_REQUEST):
            result = submit_indexnow_urls(
                urls[offset : offset + MAX_URLS_PER_REQUEST],
                force=options["force"],
            )
            submitted += result.submitted_count
            accepted_batches += int(result.accepted)

        self.stdout.write(
            self.style.SUCCESS(
                f"IndexNow finished: submitted={submitted}, accepted_batches={accepted_batches}."
            )
        )

    @staticmethod
    def _current_urls() -> list[str]:
        urls: list[str] = []
        places = public_place_queryset(Place.objects.all()).order_by("pk")
        for place in places.iterator(chunk_size=500):
            urls.extend(place_canonical_urls(place))

        visibility = build_seo_landing_visibility(CatalogContentSettings.get_solo())
        for slug in sorted(visibility.indexable_slugs):
            urls.extend(seo_landing_canonical_urls(slug))

        return list(dict.fromkeys(urls))
