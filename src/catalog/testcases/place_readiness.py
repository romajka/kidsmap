"""Tests for the single readiness verdict shared by the form, the UI and the gate."""

import json

from django.test import TestCase

from catalog.models import Category, Place, PricingPlan, Subcategory
from catalog.services.content_quality import (
    PLACE_QUALITY_ERROR_LABELS,
    place_quality_check,
    public_place_queryset,
)
from catalog.services.place_readiness import (
    PLACE_READINESS_REQUIREMENTS,
    evaluate_place_readiness,
)
from catalog.testcases.utils import create_ready_place, ensure_quality_subcategory


class PlaceReadinessRulesTests(TestCase):
    def test_complete_card_is_ready_with_full_progress(self):
        place = create_ready_place()

        readiness = evaluate_place_readiness(place)

        self.assertTrue(readiness.is_ready)
        self.assertEqual(readiness.required_count, 12)
        self.assertEqual(readiness.completed_count, 12)
        self.assertEqual(readiness.percentage, 100)
        self.assertEqual(readiness.issues, ())

    def test_every_requirement_blocks_publication_on_its_own(self):
        cases = (
            ("name", {"name_az": ""}),
            ("description", {"description_az": ""}),
            ("category", {}),
            ("subcategory", {"subcategory": None}),
            ("region", {"district": ""}),
            ("address", {"address": ""}),
            ("coordinates", {"lat": None, "lng": None}),
            ("age", {"age_from": None}),
            ("price", {"with_pricing_plan": False, "price_from": None, "price_to": None}),
            ("phone", {"phone1": ""}),
            ("photo", {"photo": "", "cover_photo": ""}),
        )

        for code, overrides in cases:
            with self.subTest(requirement=code):
                if code == "category":
                    empty_category, _created = Category.objects.get_or_create(
                        code="", defaults={"name": "Empty category"}
                    )
                    overrides = {"category": empty_category}
                place = create_ready_place(**overrides)

                readiness = evaluate_place_readiness(place)

                self.assertFalse(readiness.is_ready)
                self.assertEqual([issue.code for issue in readiness.issues], [code])
                self.assertEqual(readiness.completed_count, 11)
                self.assertEqual(readiness.percentage, 92)

    def test_schedule_requires_at_least_one_open_day_in_weekly_mode(self):
        place = create_ready_place(with_schedule_days=False, schedule="")

        readiness = evaluate_place_readiness(place)

        self.assertEqual([issue.code for issue in readiness.issues], ["schedule"])
        self.assertIn("день", readiness.issues[0].message)

    def test_non_weekly_schedule_modes_are_satisfied_by_the_mode_itself(self):
        for mode in (
            Place.SCHEDULE_MODE_BY_APPOINTMENT,
            Place.SCHEDULE_MODE_VARIABLE,
            Place.SCHEDULE_MODE_EVENTS,
        ):
            with self.subTest(mode=mode):
                place = create_ready_place(
                    with_schedule_days=False, schedule="", schedule_mode=mode
                )

                # "By events" must not require an upcoming event.
                self.assertTrue(evaluate_place_readiness(place).is_ready)

    def test_age_needs_upper_bound_or_the_open_ended_flag(self):
        without_upper = create_ready_place(age_to=None)
        self.assertEqual(
            [issue.quality_code for issue in evaluate_place_readiness(without_upper).issues],
            ["missing_age_to"],
        )

        open_ended = create_ready_place(age_to=None, age_open_ended=True)
        self.assertTrue(evaluate_place_readiness(open_ended).is_ready)

        inverted = create_ready_place(age_from=10, age_to=4)
        self.assertEqual(
            [issue.quality_code for issue in evaluate_place_readiness(inverted).issues],
            ["invalid_age_range"],
        )

    def test_adult_classes_flag_does_not_replace_the_age_range(self):
        place = create_ready_place(age_from=None, age_to=None, offers_adult_classes=True)

        self.assertEqual([issue.code for issue in evaluate_place_readiness(place).issues], ["age"])

    def test_free_tariff_counts_as_a_price(self):
        place = create_ready_place(with_pricing_plan=False, price_from=None, price_to=None)
        self.assertFalse(evaluate_place_readiness(place).is_ready)

        PricingPlan.objects.create(
            place=place,
            product_type="lesson",
            charge_role="primary",
            price_kind="free",
            price=0,
            is_active=True,
        )
        place.refresh_from_db()

        self.assertTrue(evaluate_place_readiness(place).is_ready)

    def test_legacy_scalar_price_does_not_satisfy_the_price_item(self):
        """Old ``price_*`` values still show on the site but must be migrated."""

        place = create_ready_place(with_pricing_plan=False, price_from=80, price_to=140)

        readiness = evaluate_place_readiness(place)

        self.assertFalse(readiness.is_ready)
        issue = readiness.issues[0]
        self.assertEqual(issue.quality_code, "legacy_price_not_migrated")
        self.assertIn("перенесите", issue.message.lower())
        # Backward compatibility: the published card stays in the catalog.
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_legacy_text_schedule_does_not_satisfy_the_weekly_mode(self):
        place = create_ready_place(with_schedule_days=False, schedule="Вт/Чт 15:00-17:00")

        readiness = evaluate_place_readiness(place)

        self.assertEqual(
            [issue.quality_code for issue in readiness.issues],
            ["legacy_schedule_not_migrated"],
        )
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_a_week_closed_on_every_day_is_not_a_schedule(self):
        from catalog.services.place_schedule import parse_schedule_payload, sync_place_schedule

        place = create_ready_place(with_schedule_days=False, schedule="")
        sync_place_schedule(
            place,
            parse_schedule_payload(json.dumps([
                {"weekday": day, "is_closed": True, "is_24_hours": False, "intervals": []}
                for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
            ])),
        )

        self.assertEqual(
            [issue.code for issue in evaluate_place_readiness(place).issues], ["schedule"]
        )

    def test_short_description_is_advice_and_never_blocks(self):
        place = create_ready_place(description_az="Qısa təsvir.")

        readiness = evaluate_place_readiness(place)

        self.assertTrue(readiness.is_ready)
        self.assertEqual(readiness.completed_count, 12)
        self.assertEqual(readiness.percentage, 100)
        self.assertEqual([hint.code for hint in readiness.advice], ["description_length"])
        self.assertFalse(readiness.advice[0].blocking)
        # Advice must not leak into the blocking codes.
        self.assertNotIn("description_length", place_quality_check(place).errors)

    def test_empty_description_still_blocks(self):
        place = create_ready_place(description_az="")

        self.assertEqual(
            [issue.quality_code for issue in evaluate_place_readiness(place).issues],
            ["missing_description"],
        )

    def test_gallery_photo_does_not_replace_the_main_photo(self):
        from catalog.models import PlacePhoto

        place = create_ready_place(photo="", cover_photo="")
        PlacePhoto.objects.create(place=place, image="places/gallery-1.jpg", order=1)

        self.assertEqual(
            [issue.code for issue in evaluate_place_readiness(place).issues], ["photo"]
        )

    def test_cover_photo_is_a_temporary_bridge_and_is_reported(self):
        place = create_ready_place(photo="", cover_photo="places/covers/legacy.jpg")

        readiness = evaluate_place_readiness(place)

        self.assertTrue(readiness.is_ready)
        self.assertEqual([hint.code for hint in readiness.advice], ["cover_photo_as_main"])

    def test_subcategory_of_another_category_is_rejected(self):
        other_category, _created = Category.objects.get_or_create(code="SPRT", defaults={"name": "Sport"})
        foreign = Subcategory.objects.create(
            category=other_category, code="sprt-foreign", name="Foreign subcategory"
        )
        place = create_ready_place(subcategory=foreign)

        issues = evaluate_place_readiness(place).issues

        self.assertEqual([issue.quality_code for issue in issues], ["subcategory_mismatch"])

    def test_instagram_and_website_do_not_replace_the_phone(self):
        place = create_ready_place(phone1="", instagram="kidsmap", website="https://example.com")

        self.assertEqual([issue.code for issue in evaluate_place_readiness(place).issues], ["phone"])

    def test_every_issue_points_at_a_field_and_carries_an_instruction(self):
        place = Place.objects.create(name="Empty", category=ensure_quality_subcategory().category)

        readiness = evaluate_place_readiness(place)

        self.assertFalse(readiness.is_ready)
        for issue in readiness.issues:
            with self.subTest(issue=issue.code):
                self.assertTrue(issue.anchor)
                self.assertTrue(issue.field)
                self.assertTrue(issue.message)
                self.assertTrue(issue.blocking)
                self.assertIn(issue.section, {"basics", "pricing", "location", "media"})
                self.assertIn(issue.quality_code, PLACE_QUALITY_ERROR_LABELS)


class PlaceReadinessConsistencyTests(TestCase):
    """The contradictions this rework exists to remove."""

    def test_hundred_percent_means_the_card_may_be_published(self):
        place = create_ready_place()

        readiness = evaluate_place_readiness(place)

        self.assertEqual(readiness.percentage, 100)
        self.assertTrue(readiness.is_ready)
        self.assertTrue(place_quality_check(place).is_ready)

    def test_progress_never_reaches_hundred_while_an_issue_blocks_publication(self):
        for overrides in ({"lat": None, "lng": None}, {"subcategory": None}, {"phone1": ""}):
            with self.subTest(overrides=tuple(overrides)):
                place = create_ready_place(**overrides)

                readiness = evaluate_place_readiness(place)

                self.assertLess(readiness.percentage, 100)
                self.assertFalse(place_quality_check(place).is_ready)

    def test_quality_check_reports_exactly_the_readiness_codes(self):
        place = create_ready_place(phone1="", lat=None, lng=None)

        readiness = evaluate_place_readiness(place)
        quality = place_quality_check(place)

        self.assertEqual(quality.errors, readiness.quality_codes)
        self.assertEqual(quality.score, readiness.percentage)

    def test_a_ready_card_is_also_visible_in_the_public_catalog(self):
        place = create_ready_place()

        self.assertTrue(evaluate_place_readiness(place).is_ready)
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_short_description_is_published_and_reachable_in_the_catalog(self):
        """12/12 and published means the card is on the site, however short."""

        from catalog.services.content_quality import place_catalog_visibility_reasons

        place = create_ready_place(description_az="Qısa təsvir.")

        readiness = evaluate_place_readiness(place)

        self.assertTrue(readiness.is_ready)
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertEqual(place_catalog_visibility_reasons(place), ())
        # The length is still worth mentioning, without blocking anything.
        self.assertEqual([hint.code for hint in readiness.advice], ["description_length"])

    def test_requirement_codes_are_unique_and_documented(self):
        codes = [requirement.code for requirement in PLACE_READINESS_REQUIREMENTS]

        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(codes), 12)


class PlaceAdminFormReadinessTests(TestCase):
    """The publish gate in the admin form speaks the same language as the UI."""

    def _payload(self, place, **overrides):
        data = {
            "name": place.name,
            "name_az": place.name_az,
            "name_ru": place.name_ru,
            "name_en": place.name_en,
            "description_az": place.description_az,
            "description_ru": place.description_ru,
            "description_en": place.description_en,
            "category": place.category_id,
            "subcategory": place.subcategory_id or "",
            "region": "baku",
            "district": "baku_yasamal",
            "metro": "",
            "address": place.address,
            "lat": place.lat,
            "lng": place.lng,
            "age_from": place.age_from,
            "age_to": place.age_to,
            "phone1": place.phone1,
            "schedule": place.schedule,
            "schedule_mode": place.schedule_mode,
            "pricing_plans": json.dumps([{
                "product_type": "lesson",
                "charge_role": "primary",
                "price_kind": "exact",
                "price": "80",
                "currency": "AZN",
                "is_active": True,
            }]),
            "status": Place.STATUS_PUBLISHED,
            "is_active": "on",
        }
        data.update(overrides)
        return data

    def test_publish_is_refused_with_the_concrete_missing_items(self):
        from catalog.domain_admin.place import PlaceAdminForm

        # A card that is not live yet: the compatibility mode must not apply.
        place = create_ready_place(status=Place.STATUS_DRAFT, is_active=False)
        form = PlaceAdminForm(
            data=self._payload(place, phone1="", lat="", lng=""),
            instance=place,
        )

        self.assertFalse(form.is_valid())
        summary = " ".join(form.errors.get("__all__", []))
        self.assertIn("Карточка не может быть опубликована", summary)
        self.assertIn("10 из 12 обязательных пунктов", summary)
        # Labels are localized, so pin the verdict on the codes and check that
        # the message actually spells the reasons out.
        self.assertEqual(
            sorted(issue.code for issue in form.place_readiness.issues),
            ["coordinates", "phone"],
        )
        for issue in form.place_readiness.issues:
            self.assertIn(issue.message, summary)
        # The same reasons are attached to the fields the editor has to fix.
        self.assertIn("phone1", form.errors)
        self.assertIn("lat", form.errors)

    def test_published_legacy_card_can_still_be_saved(self):
        """Migration must not freeze cards that are already on the site."""

        from catalog.domain_admin.place import PlaceAdminForm

        place = create_ready_place(
            with_pricing_plan=False,
            with_schedule_days=False,
            price_from=80,
            schedule="Пн-Пт 09:00-18:00",
            status=Place.STATUS_PUBLISHED,
            is_active=True,
        )
        form = PlaceAdminForm(data=self._payload(place, pricing_plans="[]"), instance=place)
        form.is_valid()

        self.assertNotIn("Карточка не может быть опубликована", " ".join(form.errors.get("__all__", [])))
        self.assertTrue(form.place_readiness_compatibility)
        self.assertEqual(
            sorted(issue.quality_code for issue in form.place_readiness.issues),
            ["legacy_price_not_migrated", "legacy_schedule_not_migrated"],
        )
        self.assertEqual(form.place_readiness.completed_count, 10)

    def test_compatibility_does_not_apply_to_a_new_card(self):
        from catalog.domain_admin.place import PlaceAdminForm

        place = Place(category=ensure_quality_subcategory().category)
        form = PlaceAdminForm(
            data={
                "name_az": "Yeni kart",
                "description_az": "Uşaqlar üçün dərslər.",
                "category": place.category_id,
                "region": "baku",
                "district": "baku_yasamal",
                "status": Place.STATUS_PUBLISHED,
                "is_active": "on",
                "pricing_plans": "[]",
            },
            instance=place,
        )

        self.assertFalse(form.is_valid())
        self.assertFalse(form.place_readiness_compatibility)
        self.assertIn(
            "Карточка не может быть опубликована",
            " ".join(form.errors.get("__all__", [])),
        )

    def test_unpublished_legacy_card_needs_a_full_readiness_again(self):
        from catalog.domain_admin.place import PlaceAdminForm

        place = create_ready_place(
            with_pricing_plan=False,
            with_schedule_days=False,
            price_from=80,
            schedule="Пн-Пт 09:00-18:00",
            status=Place.STATUS_DRAFT,
            is_active=False,
        )
        form = PlaceAdminForm(
            data=self._payload(place, pricing_plans="[]", status=Place.STATUS_PUBLISHED),
            instance=place,
        )

        self.assertFalse(form.is_valid())
        self.assertFalse(form.place_readiness_compatibility)
        self.assertIn(
            "Карточка не может быть опубликована",
            " ".join(form.errors.get("__all__", [])),
        )

    def test_draft_save_is_not_blocked_by_publication_requirements(self):
        from catalog.domain_admin.place import PlaceAdminForm

        place = create_ready_place()
        form = PlaceAdminForm(
            data=self._payload(place, phone1="", lat="", lng="", _save_draft="1"),
            instance=place,
        )
        form.is_valid()

        self.assertNotIn(
            "Карточка не может быть опубликована",
            " ".join(form.errors.get("__all__", [])),
        )

    def test_form_readiness_matches_the_saved_card(self):
        from catalog.domain_admin.place import PlaceAdminForm

        place = create_ready_place()
        form = PlaceAdminForm(data=self._payload(place, subcategory=""), instance=place)
        form.is_valid()

        # The verdict is decided once, in clean(), and kept: re-deriving it from
        # cleaned_data after validation would read the stored subcategory back
        # (an errored field is dropped from cleaned_data) and call the card ready.
        self.assertEqual([issue.code for issue in form.place_readiness.issues], ["subcategory"])
        self.assertEqual(form.place_readiness.completed_count, 11)
        self.assertEqual(
            [item["code"] for item in self._summary(form, place)["missing"]],
            ["subcategory"],
        )

    def _summary(self, form, place):
        from catalog.domain_admin.place import PlaceAdmin
        from django.contrib.admin.sites import AdminSite

        admin_instance = PlaceAdmin(Place, AdminSite())
        return admin_instance._build_place_form_summary(form=form, obj=place)
