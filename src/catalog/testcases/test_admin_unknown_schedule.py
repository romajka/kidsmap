"""Unknown hours must not become an explicitly closed week."""
import json

from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from catalog.forms import PlaceScheduleEditorFormMixin
from catalog.models import Place
from catalog.services.place_readiness import readiness_data_from_place
from catalog.services.place_schedule import (
    build_open_status, build_public_schedule_summary, parse_schedule_payload,
    serialize_place_schedule, sync_place_schedule, validate_schedule_payload,
)
from catalog.services.seo import build_place_seo_payload


class ScheduleForm(PlaceScheduleEditorFormMixin, forms.Form):
    schedule = forms.CharField(required=False)
    schedule_mode = forms.ChoiceField(required=False)

    def __init__(self, *args, instance, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self._init_schedule_editor()

    def clean(self):
        return self._clean_schedule_editor(super().clean())


class UnknownScheduleParsingTests(SimpleTestCase):
    def test_empty_validation_keeps_unknown_instead_of_fabricating_closed_week(self):
        self.assertEqual(validate_schedule_payload([]).days, [])
        self.assertEqual(parse_schedule_payload(None), [])


class UnknownScheduleTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Schedule fixture", name_az="Schedule fixture", category="EDU",
            is_active=False, status=Place.STATUS_DRAFT,
        )

    def test_empty_export_and_validation_do_not_invent_closed_days(self):
        self.assertEqual(serialize_place_schedule(self.place), [])
        self.assertEqual(serialize_place_schedule(Place()), [])
        for raw in (None, "", [], "[]", {"days": []}):
            with self.subTest(raw=raw):
                result = validate_schedule_payload(raw)
                self.assertEqual(result.errors, {})
                self.assertEqual(result.days, [])
                self.assertEqual(parse_schedule_payload(raw), [])

    def test_explicit_closed_week_survives_save_and_differs_from_unknown(self):
        closed = [{"weekday": day, "is_closed": True, "is_24_hours": False,
                   "intervals": []} for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")]
        sync_place_schedule(self.place, closed)
        self.assertEqual(self.place.schedule_days.count(), 7)
        self.assertEqual(serialize_place_schedule(self.place), closed)
        self.assertIn("Закрыто", build_public_schedule_summary(self.place, "ru"))
        self.assertIs(build_open_status(self.place, "ru")["is_open"], False)
        sync_place_schedule(self.place, [])
        self.assertEqual(serialize_place_schedule(self.place), [])
        self.assertEqual(build_public_schedule_summary(self.place, "ru"), "")
        self.assertEqual(build_open_status(self.place, "ru"), {})

    def test_blank_form_keeps_empty_payload_but_has_editable_day_rows(self):
        form = ScheduleForm(instance=self.place)
        self.assertEqual(json.loads(form.fields["structured_schedule"].initial), [])
        self.assertEqual(len(form.schedule_editor_days), 7)
        self.assertTrue(all(day["is_unknown"] for day in form.schedule_editor_days))
        bound = ScheduleForm(data={"schedule_mode": "regular", "structured_schedule": "[]"},
                             instance=self.place)
        self.assertTrue(bound.is_valid(), bound.errors)
        bound.save_schedule(self.place)
        self.assertEqual(self.place.schedule_days.count(), 0)

    def test_admin_json_export_distinguishes_unknown_and_explicit_closed(self):
        actor = get_user_model().objects.create_superuser(
            "schedule-export", "schedule-export@example.invalid", "synthetic")
        self.client.force_login(actor)
        url = reverse("admin:catalog_place_export_json", args=[self.place.pk])
        empty = self.client.get(url)
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["schedule_days"], [])
        sync_place_schedule(self.place, [{"weekday": "mon", "is_closed": True}])
        closed = self.client.get(url)
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(len(closed.json()["schedule_days"]), 7)
        self.assertTrue(all(day["is_closed"] for day in closed.json()["schedule_days"]))

    def test_unknown_hours_are_not_ready_or_advertised_in_schema(self):
        self.assertFalse(readiness_data_from_place(self.place).schedule_has_structured)
        request = RequestFactory().get("/", HTTP_HOST="testserver")
        payload = build_place_seo_payload(self.place, request, "az")
        self.assertNotIn("openingHoursSpecification", json.dumps(payload))
        self.assertEqual(build_open_status(self.place, "az"), {})

    def test_partial_week_preserves_existing_missing_days_closed_contract(self):
        sync_place_schedule(self.place, [{"weekday": "mon", "is_closed": False,
                                         "intervals": [{"start": "09:00", "end": "18:00"}]}])
        days = serialize_place_schedule(self.place)
        self.assertEqual(len(days), 7)
        self.assertEqual(days[0]["intervals"], [{"start": "09:00", "end": "18:00"}])
        self.assertTrue(all(day["is_closed"] for day in days[1:]))
