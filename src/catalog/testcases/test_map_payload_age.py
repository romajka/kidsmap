"""Public map ages follow card semantics, including exact offer matches."""
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.utils import timezone

from catalog.models import Activity, Location, OfferingGroup, Place, PricingPlan
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.catalog_structure import bind_confirmed_location
from catalog.services.filtering import PlaceListFilters
from catalog.services.map_payload import serialize_map_places
from catalog.testcases.utils import create_quality_place


class MapAgePayloadTests(TestCase):
    def payload(self, language="en", **params):
        filters = PlaceListFilters.from_request(RequestFactory().get("/", params))
        return serialize_map_places(
            DjangoPlaceRepository().active_queryset(), language, filters=filters
        )

    def test_place_age_is_localized_and_unknown_age_has_no_claim(self):
        ranged = create_quality_place(age_from=0, age_to=6)
        open_ended = create_quality_place(age_from=12, age_to=None)
        unknown = create_quality_place(age_from=None, age_to=None)
        for language, unit in (("az", "yaş"), ("ru", "лет"), ("en", "years")):
            with self.subTest(language=language):
                points = {point["id"]: point for point in self.payload(language)}
                self.assertEqual(points[ranged.pk].get("age"), f"0–6 {unit}")
                self.assertEqual(points[open_ended.pk].get("age"), f"12+ {unit}")
                self.assertIn(unknown.pk, points)
                self.assertEqual(points[unknown.pk]["age"], "")
                self.assertEqual(points[unknown.pk]["members"][0]["age"], "")
                self.assertEqual(points[ranged.pk]["members"][0].get("age"), f"0–6 {unit}")

    def test_each_shared_venue_member_keeps_its_own_age(self):
        venue = Location.objects.create(
            address="Synthetic shared venue", lat=40.42, lng=49.88,
            confirmed_at=timezone.now(),
        )
        younger = create_quality_place(age_from=4, age_to=6)
        older = create_quality_place(age_from=9, age_to=15)
        for place in (younger, older):
            bind_confirmed_location(place.pk, venue.pk, expected_content_version=place.content_version)
        points = self.payload()
        self.assertEqual(len(points), 1)
        self.assertEqual(
            {member["id"]: member.get("age") for member in points[0]["members"]},
            {younger.pk: "4–6 years", older.pk: "9–15 years"},
        )

    def test_exact_age_filter_does_not_present_broad_place_age_or_other_group(self):
        place = create_quality_place(age_from=0, age_to=18)
        for low, high, amount in ((4, 6, "25"), (10, 15, "120")):
            activity = Activity.objects.create(
                place=place, status="published", name_az=f"Lessons {low}",
                program_snapshot={"category_id": place.category_id},
            )
            group = OfferingGroup.objects.create(
                activity=activity, name_az=f"Group {low}", age_from=low, age_to=high,
            )
            PricingPlan.objects.create(
                offering_group=group, product_type="lesson", price=Decimal(amount),
            )
        member = self.payload(age="5")[0]["members"][0]
        self.assertEqual(member.get("age"), "")
        self.assertEqual(
            [group["age"] for offer in member["matched_offers"] for group in offer["groups"]],
            ["4–6"],
        )
        self.assertIn("25", member["price"])
        self.assertNotIn("120", member["price"])

    def test_public_boundary_and_localized_urls_remain_intact(self):
        public = create_quality_place(name_az="Visible fixture", phone1="+994500001234")
        create_quality_place(name_az="Private draft", status=Place.STATUS_DRAFT)
        for language in ("az", "ru", "en"):
            with self.subTest(language=language):
                points = self.payload(language)
                self.assertEqual([point["id"] for point in points], [public.pk])
                member = points[0]["members"][0]
                if language == "az":
                    self.assertTrue(member["url"].startswith("/place/"))
                else:
                    self.assertTrue(member["url"].startswith(f"/{language}/"))
                self.assertTrue(member["has_phone"])
                self.assertNotIn("phone1", member)
                self.assertNotIn("phones", member)
                self.assertNotIn("owner", member)
                self.assertNotIn("revision", member)
