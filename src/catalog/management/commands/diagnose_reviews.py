"""
Diagnostic command to investigate why reviews are not showing on the public site.

Usage:
    python manage.py diagnose_reviews
    python manage.py diagnose_reviews --fix-pending

On server:
    docker compose exec -T web python manage.py diagnose_reviews
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db.models.functions import Length


class Command(BaseCommand):
    help = "Diagnose why reviews are not showing on the public site"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-pending",
            action="store_true",
            default=False,
            help="Auto-approve PlaceReviews and SiteReviews that are stuck in 'pending' but pass quality checks",
        )

    def handle(self, *args, **options):
        from catalog.models import PlaceReview, SiteReview
        from catalog.services.content_quality import (
            public_review_queryset,
            approved_review_queryset,
        )

        fix = options["fix_pending"]

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== PlaceReview Diagnosis ==="))

        total = PlaceReview.objects.count()
        self.stdout.write(f"Total PlaceReviews: {total}")

        # Status breakdown
        for row in PlaceReview.objects.values("status", "is_approved").annotate(n=Count("id")).order_by("status"):
            self.stdout.write(f"  status={row['status']!r:12s} is_approved={row['is_approved']}  count={row['n']}")

        # How many pass public filter
        public_count = public_review_queryset(PlaceReview.objects.all()).count()
        self.stdout.write(f"\nPassing public_review_queryset (visible on site): {public_count}")

        if public_count == 0 and total > 0:
            self.stdout.write(self.style.WARNING("  ⚠ Reviews exist but NONE are visible publicly!"))
            self._diagnose_place_reviews(fix=fix)
        elif public_count < total:
            self.stdout.write(self.style.WARNING(f"  ⚠ Only {public_count}/{total} reviews are visible publicly."))
            self._diagnose_place_reviews(fix=fix)
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ All {total} reviews are visible publicly."))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SiteReview Diagnosis ==="))

        sr_total = SiteReview.objects.count()
        self.stdout.write(f"Total SiteReviews: {sr_total}")

        for row in SiteReview.objects.values("status", "is_approved").annotate(n=Count("id")).order_by("status"):
            self.stdout.write(f"  status={row['status']!r:12s} is_approved={row['is_approved']}  count={row['n']}")

        sr_visible = approved_review_queryset(SiteReview.objects.all()).exclude(text="").count()
        self.stdout.write(f"\nPassing approved+non-empty filter (visible on site): {sr_visible}")

        if sr_visible == 0 and sr_total > 0:
            self.stdout.write(self.style.WARNING("  ⚠ SiteReviews exist but NONE are visible publicly!"))
            self._diagnose_site_reviews(fix=fix)
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ {sr_visible} SiteReviews are visible."))

        self.stdout.write("")

    def _diagnose_place_reviews(self, *, fix: bool):
        from catalog.models import PlaceReview

        qs = PlaceReview.objects.annotate(review_text_len=Length("text"))

        # Step 1: status filter
        not_approved_status = qs.exclude(status="approved").count()
        not_approved_flag = qs.exclude(is_approved=True).count()
        self.stdout.write(f"\n  Breakdown of why reviews are filtered out:")
        self.stdout.write(f"    status != 'approved': {not_approved_status}")
        self.stdout.write(f"    is_approved != True:  {not_approved_flag}")

        # Step 2: rating filter
        bad_rating = qs.filter(status="approved", is_approved=True).filter(
            Q(rating__lt=1) | Q(rating__gt=5)
        ).count()
        self.stdout.write(f"    bad rating (<1 or >5): {bad_rating}")

        # Step 3: text too short
        too_short = qs.filter(status="approved", is_approved=True).filter(review_text_len__lt=20).count()
        self.stdout.write(f"    text too short (<20 chars): {too_short}")

        # Step 4: junk tokens
        junk_q = Q()
        for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
            junk_q |= Q(text__icontains=token) | Q(author_name__icontains=token)
        junk_count = qs.filter(status="approved", is_approved=True).filter(junk_q).count()
        self.stdout.write(f"    junk/test content: {junk_count}")

        # Sample of pending reviews
        pending_reviews = PlaceReview.objects.filter(status="pending").select_related("place")[:5]
        if pending_reviews:
            self.stdout.write(f"\n  Sample PENDING reviews (first 5):")
            for r in pending_reviews:
                self.stdout.write(
                    f"    id={r.id}, place={r.place_id}, rating={r.rating}, "
                    f"len(text)={len(r.text)}, author={r.author_name!r}"
                )

        # Fix option
        if fix:
            self.stdout.write(self.style.MIGRATE_HEADING("\n  Applying --fix-pending..."))
            candidate_qs = (
                PlaceReview.objects
                .annotate(review_text_len=Length("text"))
                .filter(status="pending", is_approved=False)
                .filter(review_text_len__gte=20)
                .filter(rating__gte=1, rating__lte=5)
            )
            junk_q = Q()
            for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
                junk_q |= Q(text__icontains=token) | Q(author_name__icontains=token)
            candidate_qs = candidate_qs.exclude(junk_q)
            fixed = candidate_qs.update(status="approved", is_approved=True)
            self.stdout.write(self.style.SUCCESS(f"  Fixed {fixed} PlaceReview(s): status set to 'approved'."))

    def _diagnose_site_reviews(self, *, fix: bool):
        from catalog.models import SiteReview

        qs = SiteReview.objects.all()

        not_approved_status = qs.exclude(status="approved").count()
        not_approved_flag = qs.exclude(is_approved=True).count()
        empty_text = qs.filter(status="approved", is_approved=True, text="").count()
        self.stdout.write(f"\n  Breakdown of why SiteReviews are filtered out:")
        self.stdout.write(f"    status != 'approved': {not_approved_status}")
        self.stdout.write(f"    is_approved != True:  {not_approved_flag}")
        self.stdout.write(f"    empty text:           {empty_text}")

        pending = SiteReview.objects.filter(status="pending")[:5]
        if pending:
            self.stdout.write(f"\n  Sample PENDING SiteReviews (first 5):")
            for r in pending:
                self.stdout.write(f"    id={r.id}, rating={r.rating}, len(text)={len(r.text)}, author={r.author_name!r}")

        if fix:
            self.stdout.write(self.style.MIGRATE_HEADING("\n  Applying --fix-pending for SiteReviews..."))
            from django.db.models.functions import Length as Len
            candidate_qs = (
                SiteReview.objects
                .annotate(tlen=Len("text"))
                .filter(status="pending", is_approved=False)
                .filter(tlen__gte=20)
                .filter(rating__gte=1, rating__lte=5)
            )
            junk_q = Q()
            for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
                junk_q |= Q(text__icontains=token) | Q(author_name__icontains=token)
            candidate_qs = candidate_qs.exclude(junk_q)
            fixed = candidate_qs.update(status="approved", is_approved=True)
            self.stdout.write(self.style.SUCCESS(f"  Fixed {fixed} SiteReview(s): status set to 'approved'."))
