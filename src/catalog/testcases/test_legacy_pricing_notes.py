from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory
from django.utils.translation import override
from django.conf import settings
from django.http import HttpResponse
from config.middleware import AdminLocaleMiddleware

from catalog.domain_admin.place import PlaceAdmin
from catalog.models import Place
from catalog.services.volunteer_places import content_snapshot, candidate_from_payload


class LegacyPricingNotesTests(SimpleTestCase):
    def test_place_editor_honors_azerbaijani_language_picker(self):
        request = RequestFactory().get('/admin/catalog/place/1/change/')
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'az'
        response = AdminLocaleMiddleware(lambda req: HttpResponse(req.LANGUAGE_CODE))(request)
        self.assertEqual(response.content, b'az')

    def test_admin_exposes_legacy_fields(self):
        request = RequestFactory().get('/admin/')
        request.user = get_user_model()(is_staff=True, is_superuser=True, is_active=True)
        form = PlaceAdmin(Place, AdminSite()).get_form(request, Place())
        self.assertIn('additional_info', form.base_fields)
        self.assertIn('extra_conditions', form.base_fields)

    def test_legacy_notes_round_trip_and_clear_in_shared_snapshot(self):
        place = Place(additional_info='Group 1\nMonday 16:00', extra_conditions='Booking')
        snapshot = content_snapshot(place)
        self.assertEqual(snapshot['additional_info'], place.additional_info)
        snapshot.update(additional_info='', extra_conditions='')
        candidate = candidate_from_payload(place, snapshot)
        self.assertEqual(candidate.additional_info_i18n('ru'), '')
        self.assertEqual(candidate.extra_conditions_i18n('ru'), '')

    def test_legacy_fallback_is_ru_only(self):
        place = Place(additional_info='Legacy', additional_info_az='AZ', additional_info_en='EN')
        for lang, expected in [('ru', 'Legacy'), ('az', 'AZ'), ('en', 'EN')]:
            self.assertEqual(place.additional_info_i18n(lang), expected)

    def test_public_notes_and_disclaimer(self):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang), override(lang):
                place = Place(**{f'additional_info_{lang}': 'Line one\n<script>two</script>'})
                context = {'place': place, 'pricing_summary': {'has_price': True}}
                html = render_to_string('catalog/includes/pricing_notes.html', context)
                self.assertIn('Line one<br>', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertIn('data-price-disclaimer', html)
                place.is_verified = True
                html = render_to_string('catalog/includes/pricing_notes.html', context)
                self.assertNotIn('data-price-disclaimer', html)
                self.assertIn('Line one', html)

    def test_no_disclaimer_without_pricing(self):
        html = render_to_string('catalog/includes/pricing_notes.html', {'place': Place(), 'pricing_summary': {}})
        self.assertNotIn('data-price-disclaimer', html)
