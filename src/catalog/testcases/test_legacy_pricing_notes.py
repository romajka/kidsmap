from datetime import timedelta
import json

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory, TestCase
from django.utils import timezone
from django.utils.translation import override
from django.conf import settings
from django.http import HttpResponse
from config.middleware import AdminLocaleMiddleware

from catalog.domain_admin.place import PlaceAdmin, PlaceAdminForm
from catalog.models import Activity, OfferingGroup, Place, PricingPlan
from catalog.services import publication
from catalog.services.place_schedule import dump_schedule_payload, serialize_place_schedule
from catalog.services.pricing_plans import replace_place_pricing_plans, serialize_pricing_plan
from catalog.services.publication_forms import save_form, version_token
from catalog.services.volunteer_places import content_snapshot, candidate_from_payload
from catalog.testcases.utils import create_ready_place


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
                context = {'place': place, 'pricing_summary': {'has_price': True, 'show_price_disclaimer': True}}
                html = render_to_string('catalog/includes/pricing_notes.html', context)
                self.assertIn('Line one<br>', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertIn('data-price-disclaimer', html)
                place.is_verified = True
                html = render_to_string('catalog/includes/pricing_notes.html', context)
                # Retired listing badge no longer suppresses the price caution.
                self.assertIn('data-price-disclaimer', html)
                self.assertIn('Line one', html)

    def test_no_disclaimer_without_pricing(self):
        html = render_to_string('catalog/includes/pricing_notes.html', {'place': Place(), 'pricing_summary': {}})
        self.assertNotIn('data-price-disclaimer', html)


class VerifiedPricingNotesTests(TestCase):
    source = 'https://example.com/tickets'

    def setUp(self):
        self.place = create_ready_place()
        self.plan = self.place.pricing_plan_records.first()
        self.plan.source_url = self.source
        self.plan.verified_at = timezone.now() - timedelta(days=1)
        self.plan.save()

    def assert_public_warning(self, expected):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(self.place.get_absolute_url())
                if expected:
                    self.assertContains(response, 'data-price-disclaimer')
                else:
                    self.assertNotContains(response, 'data-price-disclaimer')

    def test_every_visible_tariff_requires_independent_proof(self):
        self.assert_public_warning(False)
        activity = Activity.objects.create(place=self.place, name_az='QA')
        Activity.objects.filter(pk=activity.pk).update(status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='QA group')
        plan = PricingPlan.objects.create(
            offering_group=group, product_type='lesson', price=25,
            source_url=self.source, verified_at=timezone.now() + timedelta(days=1),
        )
        self.assert_public_warning(True)
        plan.verified_at = timezone.now() - timedelta(hours=1)
        plan.source_url = ''
        plan.save()
        self.assert_public_warning(True)
        plan.valid_until = timezone.localdate() - timedelta(days=1)
        plan.save()
        self.assert_public_warning(False)

    def test_legacy_price_with_forged_proof_keeps_warning(self):
        self.plan.delete()
        Place.objects.filter(pk=self.place.pk).update(
            pricing_plans_legacy=[{'product_type': 'lesson', 'price': '80',
                                   'source_url': self.source, 'verified_at': timezone.now().isoformat()}],
        )
        self.assert_public_warning(True)

    def test_new_price_or_source_requires_current_staff_verification(self):
        raw = serialize_pricing_plan(self.plan)
        raw['title_ru'] = 'Updated translation'
        updated, = replace_place_pricing_plans(self.place, [raw], allow_verified=True)
        self.assertEqual(updated.verified_at, self.plan.verified_at)
        raw.update(price='29.00')
        updated, = replace_place_pricing_plans(self.place, [raw], allow_verified=True)
        self.assertIsNone(updated.verified_at)
        self.assert_public_warning(True)
        raw.update(verified_at=(timezone.now() - timedelta(hours=1)).isoformat())
        replace_place_pricing_plans(self.place, [raw], allow_verified=True)
        self.assert_public_warning(False)
        raw.update(source_url='https://example.com/different-tickets')
        replace_place_pricing_plans(self.place, [raw])
        self.assert_public_warning(True)

    def test_publishers_can_save_price_verification_through_the_publication_pipeline(self):
        staff = get_user_model().objects.create_superuser(username='price-proof-publisher')
        place = self.place
        place.refresh_from_db()
        new_source = 'https://example.com/current-tickets'
        new_date = timezone.now() - timedelta(hours=1)
        raw = {**serialize_pricing_plan(self.plan), 'source_url': new_source, 'verified_at': new_date.isoformat()}
        revision = publication.propose(
            actor=staff, target_type='place', target_id=place.pk, patch={'pricing_plans': [raw]},
            schema_version=publication.SCHEMA_VERSION, expected_version=place.content_version,
        )
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.source_url, self.source)
        publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.plan.refresh_from_db()
        self.assertEqual((self.plan.source_url, self.plan.verified_at), (new_source, new_date))
        self.assert_public_warning(False)

    def test_owner_cannot_certify_a_new_price_through_publication(self):
        owner = get_user_model().objects.create_user(username='price-proof-owner')
        Place.objects.filter(pk=self.place.pk).update(owner=owner)
        self.place.refresh_from_db()
        raw = {**serialize_pricing_plan(self.plan), 'price': '45.00',
               'verified_at': (timezone.now() - timedelta(hours=1)).isoformat()}
        publication.propose(
            actor=owner, target_type='place', target_id=self.place.pk, patch={'pricing_plans': [raw]},
            schema_version=publication.SCHEMA_VERSION, expected_version=self.place.content_version,
        )
        self.plan.refresh_from_db()
        self.assertEqual(str(self.plan.price), '45.00')
        self.assertIsNone(self.plan.verified_at)
        self.assert_public_warning(True)

    def test_admin_can_save_and_clear_translated_notes_and_legacy_russian_text(self):
        staff = get_user_model().objects.create_superuser(username='pricing-notes-editor')
        place = self.place
        notes = {'az': 'QA qrup saatı', 'ru': 'QA время группы', 'en': 'QA group hours'}
        for clear in (False, True):
            place.refresh_from_db()
            data = model_to_dict(place)
            data.update(
                region='baku', district=place.district, category=place.category_id,
                publication_token=version_token(place),
                pricing_plans=json.dumps(place.pricing_plans),
                structured_schedule=dump_schedule_payload(serialize_place_schedule(place)),
                additional_info='' if clear else 'QA legacy schedule',
            )
            for lang, note in notes.items():
                data[f'additional_info_{lang}'] = '' if clear else note
                data[f'extra_conditions_{lang}'] = '' if clear else f'QA terms {lang}'
            form = PlaceAdminForm(data=data, instance=place)
            self.assertTrue(form.is_valid(), form.errors.as_json())
            revision = save_form(actor=staff, form=form)
            publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
            for lang, note in notes.items():
                with self.subTest(lang=lang, clear=clear), override(lang):
                    response = self.client.get(place.get_absolute_url())
                    if clear:
                        self.assertNotContains(response, note)
                        self.assertNotContains(response, f'QA terms {lang}')
                        self.assertNotContains(response, 'QA legacy schedule')
                    else:
                        self.assertContains(response, note)
                        self.assertContains(response, f'QA terms {lang}')
