from django.core.management.base import BaseCommand

from catalog.models import Place, PlaceReview, SiteReview
from catalog.services.content_quality import contains_test_content, place_quality_check, review_quality_check


class Command(BaseCommand):
    help = "Audit KidsMap public content quality before publishing."

    def handle(self, *args, **options):
        issues: list[str] = []

        for place in Place.objects.prefetch_related("gallery").all().order_by("id"):
            check = place_quality_check(place)
            if check.errors:
                issues.append(f"place:{place.pk} {place.name_i18n('az') or place.name} -> {', '.join(check.errors)}")
            if place.status == Place.STATUS_PUBLISHED and not check.is_ready:
                issues.append(f"place:{place.pk} published_below_quality_score={check.score}")
            if any(
                contains_test_content(value)
                for value in (
                    place.name,
                    place.name_ru,
                    place.name_az,
                    place.name_en,
                    place.description_ru,
                    place.description_az,
                    place.description_en,
                    place.schedule,
                    place.address,
                )
            ):
                issues.append(f"place:{place.pk} contains_test_content")

        for review in PlaceReview.objects.select_related("place").all().order_by("id"):
            check = review_quality_check(review)
            if check.errors:
                issues.append(f"place_review:{review.pk} place={review.place_id} -> {', '.join(check.errors)}")
            if review.status == PlaceReview.STATUS_APPROVED and not check.is_ready:
                issues.append(f"place_review:{review.pk} approved_below_quality_score={check.score}")

        for review in SiteReview.objects.all().order_by("id"):
            check = review_quality_check(review)
            if check.errors:
                issues.append(f"site_review:{review.pk} -> {', '.join(check.errors)}")
            if review.status == SiteReview.STATUS_APPROVED and not check.is_ready:
                issues.append(f"site_review:{review.pk} approved_below_quality_score={check.score}")

        if not issues:
            self.stdout.write(self.style.SUCCESS("Content audit passed: no critical issues found."))
            return

        self.stdout.write(self.style.WARNING(f"Content audit found {len(issues)} issue(s)."))
        for issue in issues:
            self.stdout.write(f"- {issue}")
        self.stdout.write("Recommendations: move junk/incomplete records to draft/rejected, fill required fields, approve only moderated reviews.")
