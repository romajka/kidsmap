"""Admin lists and editors must measure the same saved working copy."""
import json
from html.parser import HTMLParser

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Place, PlaceOwnershipRequest, VolunteerPlaceRevision, Activity, OfferingGroup, PricingPlan, SiteSettings
from catalog.services import publication
from catalog.services.place_readiness import evaluate_place_readiness
from catalog.testcases.utils import create_ready_place, main_photo_upload


class ReadinessTriggers(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.rows = {}; self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'data-readiness-trigger' in values:
            self.rows[values['data-place-id']] = values


class AdminSavedReadinessTests(TestCase):
    def setUp(self):
        # The read-only GET test needs the normal singleton to exist already.
        SiteSettings.get_solo()
        self.staff = get_user_model().objects.create_superuser(
            'readiness-staff', 'readiness@example.invalid', 'fictional')
        self.owner = get_user_model().objects.create_user('readiness-owner')
        ready = create_ready_place(district='baku_nasimi', photo=main_photo_upload())
        self.subcategory = ready.subcategory
        self.photo_name = ready.photo.name
        self.place = Place.objects.create(name='Batut Arena Baku', name_az='Batut Arena Baku',
            category=ready.category, owner=self.owner, status='draft', is_active=False)
        self.client.force_login(self.staff)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'
        self.list_url = reverse('admin:catalog_place_changelist')
        self.edit_url = reverse('admin:catalog_place_change', args=[self.place.pk])

    def save_candidate(self, **overrides):
        patch = dict(description_az='Ailəvi oyun və əyləncə məkanı.',
            subcategory=self.subcategory.pk, district='baku_nasimi',
            address='Bakı, Zabitlər parkı', lat=40.4, lng=49.8, phone1='+994501112233',
            schedule_mode='by_appointment', photo=self.photo_name)
        patch.update(overrides)
        return publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch=patch, schema_version=1, expected_version=self.place.content_version,
            submit=False, explicit_save=False)

    def trigger(self, url=None):
        response = self.client.get(url or self.list_url)
        self.assertEqual(response.status_code, 200)
        return ReadinessTriggers(response.content.decode()).rows[str(self.place.pk)]

    def test_saved_readiness_matches_editor_list_and_request_list(self):
        self.save_candidate()
        PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner, request_kind='PUBLICATION')
        self.assertEqual(evaluate_place_readiness(self.place).percentage, 17)
        for language in ('az', 'ru', 'en'):
            with self.subTest(language=language), override(language):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
                editor = self.client.get(self.edit_url)
                summary = editor.context['km_place_form_summary']
                self.assertEqual(summary['completion_pct'], 83)
                for url in (self.list_url, reverse('admin:catalog_placeownershiprequest_changelist')):
                    row = self.trigger(url)
                    self.assertEqual((row['data-score'], row['data-done'], row['data-total']), ('83', '10', '12'))
                    missing = {item['code'] for item in json.loads(row['data-readiness']) if not item['done']}
                    self.assertEqual(missing, {'age', 'price'})
        self.place.refresh_from_db()
        self.assertEqual(self.place.description_az, '')
        self.assertEqual(self.place.status, 'draft')

    def test_active_revision_statuses_use_saved_values_approved_and_declined_use_live(self):
        revision = self.save_candidate()
        for status, expected in (('draft', '83'), ('pending', '83'), ('rejected', '83'),
                                 ('approved', '17'), ('declined', '17')):
            with self.subTest(status=status):
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=status)
                self.assertEqual(self.trigger()['data-score'], expected)

    def test_explicit_clear_of_saved_fields_reduces_both_editor_and_list(self):
        self.place.description_az='Dərslər'; self.place.address='Bakı, Nizami 10'
        self.place.save(update_fields=['description_az', 'address'])
        self.save_candidate(description_az='', address='')
        summary = self.client.get(self.edit_url).context['km_place_form_summary']
        self.assertEqual(summary['completion_pct'], 67)
        self.assertEqual(self.trigger()['data-score'], '67')

    def test_candidate_price_and_schedule_clear_are_counted(self):
        revision = self.save_candidate(age_from=5, age_to=12,
            pricing_plans=[{'product_type':'visit', 'price':25}],
            schedule_mode='regular', structured_schedule=[])
        self.assertEqual(self.trigger()['data-score'], '92')
        row = self.trigger()
        self.assertEqual({i['code'] for i in json.loads(row['data-readiness']) if not i['done']}, {'schedule'})
        self.assertEqual(self.client.get(self.edit_url).context['km_place_form_summary']['completion_pct'], 92)

    def test_list_get_with_candidate_is_read_only(self):
        self.save_candidate()
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
            self.assertEqual(self.trigger()['data-score'], '83')

    def test_no_candidate_keeps_current_card_readiness(self):
        self.assertEqual(self.trigger()['data-score'], '17')

    def test_non_baku_city_remains_complete_after_reload(self):
        self.save_candidate(district='ganja')
        summary = self.client.get(self.edit_url).context['km_place_form_summary']
        self.assertEqual(summary['completion_pct'], 83)
        self.assertEqual(self.trigger()['data-score'], '83')

    def test_nested_candidate_price_is_counted_and_explicit_empty_tree_removes_it(self):
        from catalog.services.pricing_plans import serialize_nested_pricing
        activity = Activity.objects.create(place=self.place, name_az='Oyun', status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='Qrup')
        PricingPlan.objects.create(offering_group=group, product_type='visit', price=25)
        revision = self.save_candidate(age_from=5, age_to=12,
            nested_pricing=serialize_nested_pricing(self.place), pricing_plans=[])
        for empty, score in ((False, '100'), (True, '92')):
            if empty:
                payload = {**revision.payload, 'nested_pricing': {'pricing_schema_version':2, 'activities':[]}}
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(payload=payload)
            with self.subTest(empty_tree=empty):
                self.assertEqual(self.trigger()['data-score'], score)
                summary = self.client.get(self.edit_url).context['km_place_form_summary']
                self.assertEqual(summary['completion_pct'], int(score))

    def test_list_publish_uses_ready_candidate_instead_of_incomplete_live_row(self):
        self.save_candidate(age_from=5, age_to=12, price_mode='free')
        VolunteerPlaceRevision.objects.filter(place=self.place).update(status='pending')
        response = self.client.post(reverse('admin:catalog_place_toggle_publication', args=[self.place.pk]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['ok'])
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'published')

    def test_volunteer_editor_counts_saved_structured_hours(self):
        from catalog.services.volunteer_places import editor_form
        from catalog.services.volunteer_editor import editor_context
        revision = self.save_candidate(schedule_mode='regular', structured_schedule=[
            {'weekday':'mon', 'is_closed':False, 'intervals':[{'start':'10:00','end':'18:00'}]}])
        context = editor_context(editor_form(self.place, revision))
        self.assertEqual(context['editor_readiness'].percentage, 83)
        self.assertEqual(self.trigger()['data-score'], '83')

    def test_malformed_legacy_schedule_is_incomplete_without_breaking_the_list(self):
        revision = self.save_candidate(schedule_mode='regular', structured_schedule=[])
        for raw in ([None], {'days': True}, '[null]'):
            with self.subTest(raw=raw):
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(
                    payload={**revision.payload, 'structured_schedule': raw})
                row = self.trigger()
                self.assertEqual(row['data-score'], '75')
                self.assertIn('schedule', {i['code'] for i in json.loads(row['data-readiness']) if not i['done']})
