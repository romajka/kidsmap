"""Missing active RU translation must not leak AZ into the district option."""
from django import forms
from django.test import SimpleTestCase
from django.utils.translation import gettext, override

from catalog.services.locations import configure_location_choices


class LocationProbeForm(forms.Form):
    region = forms.ChoiceField(required=False)
    district = forms.ChoiceField(required=False)


class DistrictLocalizationTests(SimpleTestCase):
    def test_empty_option_matches_request_language(self):
        expected = {"ru": "Выберите район", "az": "Rayon seçin", "en": "Select district"}
        for language, label in expected.items():
            with self.subTest(language=language), override(language):
                form = LocationProbeForm()
                configure_location_choices(form)
                choices = list(form.fields["district"].choices)
                self.assertEqual(gettext("Выберите район"), label)
                self.assertEqual((choices[0][0], str(choices[0][1])), ("", label))
                self.assertInHTML(f'<option value="" selected>{label}</option>', str(form["district"]))

    def test_language_switch_keeps_district_values(self):
        all_values = []
        for language in ("ru", "az", "en"):
            with override(language):
                form = LocationProbeForm()
                configure_location_choices(form)
                values = [value for value, _ in form.fields["district"].choices]
                self.assertEqual(values[0], "")
                self.assertIn("baku_yasamal", values)
                self.assertEqual(form.fields["district"].clean("baku_yasamal"), "baku_yasamal")
                # Labels are intentionally sorted in the current language.
                # The submitted codes, rather than display order, stay stable.
                all_values.append(sorted(values))
        self.assertEqual(all_values[0], all_values[1])
        self.assertEqual(all_values[1], all_values[2])
