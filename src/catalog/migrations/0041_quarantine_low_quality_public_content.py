import re

from django.db import migrations


TEST_RE = re.compile(r"(^|\b)(a{3,}|test|lorem|ipsum|123456|qwerty|asdf)(\b|$)", re.IGNORECASE)


def _has_test_text(*values):
    return any(TEST_RE.search((value or "").strip()) for value in values)


def _place_has_required_public_fields(place):
    descriptions = (place.description_ru or "", place.description_az or "", place.description_en or "")
    return all(
        (
            bool(place.category),
            bool((place.address or "").strip()),
            bool((place.schedule or "").strip()),
            bool((place.phone1 or "").strip() or (place.instagram or "").strip() or (place.website or "").strip()),
            place.age_from is not None or place.age_to is not None,
            any(
                value is not None
                for value in (
                    place.price_from,
                    place.price_to,
                    place.price_per_lesson,
                    place.price_per_month,
                    place.price_per_8_lessons,
                )
            ),
            max((len(item.strip()) for item in descriptions), default=0) >= 120,
        )
    )


def quarantine_low_quality_public_content(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    PlaceReview = apps.get_model("catalog", "PlaceReview")
    SiteReview = apps.get_model("catalog", "SiteReview")

    for place in Place.objects.filter(status="published").only(
        "id",
        "name",
        "name_ru",
        "name_az",
        "name_en",
        "description_ru",
        "description_az",
        "description_en",
        "category",
        "address",
        "schedule",
        "phone1",
        "instagram",
        "website",
        "age_from",
        "age_to",
        "price_from",
        "price_to",
        "price_per_lesson",
        "price_per_month",
        "price_per_8_lessons",
        "status",
        "rejection_reason",
        "is_active",
    ):
        has_test_text = _has_test_text(
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
        if has_test_text:
            place.status = "rejected"
            place.is_active = False
            place.rejection_reason = "Automatically rejected by content quality audit: test content."
            place.save(update_fields=["status", "is_active", "rejection_reason"])
        elif not _place_has_required_public_fields(place):
            place.status = "draft"
            place.rejection_reason = "Automatically moved to draft by content quality audit: incomplete public data."
            place.save(update_fields=["status", "rejection_reason"])

    for review_model in (PlaceReview, SiteReview):
        for review in review_model.objects.filter(status="approved").only("id", "text", "author_name", "rating", "status", "is_approved", "rejection_reason"):
            text = (review.text or "").strip()
            if len(text) < 20 or _has_test_text(text, review.author_name) or not (1 <= int(review.rating or 0) <= 5):
                review.status = "rejected"
                review.is_approved = False
                review.rejection_reason = "Automatically rejected by content quality audit."
                review.save(update_fields=["status", "is_approved", "rejection_reason"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0040_content_moderation_statuses"),
    ]

    operations = [
        migrations.RunPython(quarantine_low_quality_public_content, migrations.RunPython.noop),
    ]
