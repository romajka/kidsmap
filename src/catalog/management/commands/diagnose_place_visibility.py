"""Read-only diagnosis of actual Place catalog visibility.

Usage: python manage.py diagnose_place_visibility --examples 5
"""

from collections import Counter, defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Q

from catalog.models import Place
from catalog.services.content_quality import (
    PLACE_STATUS_PUBLISHED,
    TEST_CONTENT_TOKENS,
    place_catalog_visibility_reasons,
    public_place_queryset,
)


class Command(BaseCommand):
    help = "Read-only report on Place catalog visibility, hide reasons, and junk-filter false positives."

    def add_arguments(self, parser):
        parser.add_argument("--examples", type=int, default=5, help="Maximum example IDs per section (default: 5).")

    def handle(self, *args, **options):
        limit = max(options["examples"], 0)
        published_active = Place.objects.filter(
            status=PLACE_STATUS_PUBLISHED,
            is_active=True,
            deleted_at__isnull=True,
        )
        public_ids = set(public_place_queryset(published_active).values_list("pk", flat=True))
        hidden = published_active.exclude(pk__in=public_ids)

        reason_counts = Counter()
        reason_examples = defaultdict(list)
        for place in hidden.iterator():
            reasons = place_catalog_visibility_reasons(place) or ("unknown",)
            for reason in reasons:
                reason_counts[reason] += 1
                if len(reason_examples[reason]) < limit:
                    reason_examples[reason].append(place.pk)
        # ``published_active`` is the admin's status-level claim. ``public_ids``
        # is the catalog's actual answer; their set difference is precisely the
        # mismatch operators need to inspect.
        admin_site_mismatches = list(hidden.values_list("pk", flat=True)[:limit])

        contact_junk_q = Q()
        for token in TEST_CONTENT_TOKENS:
            contact_junk_q |= Q(phone1__icontains=token) | Q(instagram__icontains=token) | Q(website__icontains=token)
        # These are cards now visible that the old contact-inclusive junk rule
        # would have excluded. No model is saved or modified by this command.
        false_positive_ids = list(
            public_place_queryset(published_active).filter(contact_junk_q).values_list("pk", flat=True)[:limit]
        )
        false_positive_count = public_place_queryset(published_active).filter(contact_junk_q).count()

        self.stdout.write(f"published+active in catalog: {len(public_ids)}")
        self.stdout.write(f"published+active hidden: {hidden.count()}")
        self.stdout.write("hide reasons:")
        if reason_counts:
            for reason, count in sorted(reason_counts.items()):
                self.stdout.write(f"  {reason}: {count}; example ids: {reason_examples[reason]}")
        else:
            self.stdout.write("  none")
        self.stdout.write(f"junk false positives (old contact rule): {false_positive_count}; example ids: {false_positive_ids}")
        self.stdout.write(f"admin ↔ site mismatches: {hidden.count()}; example ids: {admin_site_mismatches}")
