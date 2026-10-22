"""Untrusted schedule display projection must not crash before form validation."""
from django import forms
from django.test import SimpleTestCase
from catalog.models import Place
from catalog.services.permanent_place_rules import readiness_presentation_snapshot
from catalog.services.place_readiness import readiness_data_from_form


class DisplayScheduleForm(forms.Form):
    structured_schedule = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.instance = Place()
        super().__init__(*args, **kwargs)


class OwnerReadinessProjectionTests(SimpleTestCase):
    def test_malformed_schedule_snapshot_is_safe_without_changing_posted_input(self):
        for raw in ('[null]', '[{}]', '{broken', '{"days":true}', '[{"weekday":"mon","intervals":3}]'):
            with self.subTest(raw=raw):
                form = DisplayScheduleForm(data={'structured_schedule': raw})
                snapshot = readiness_presentation_snapshot(form)
                data = readiness_data_from_form(snapshot)
                self.assertFalse(data.schedule_has_structured)
                self.assertTrue(all(isinstance(day, dict) for day in snapshot.cleaned_schedule_days))
                self.assertEqual(form['structured_schedule'].value(), raw)
