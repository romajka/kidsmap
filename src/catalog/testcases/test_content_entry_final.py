"""Regressions for the remaining local content-entry acceptance defects."""
import hashlib
import json
from datetime import timedelta
from io import BytesIO

from PIL import Image
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from catalog.forms import OwnerPlaceEditForm
from catalog.models import Event, Organization, Place, PlacePhoto, Specialist, VolunteerPlaceRevision
from catalog.services import publication, publication_forms
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.volunteer_places import review_form
from catalog.testcases.utils import create_quality_place
from catalog.testcases import admin as existing_admin_tests


class CandidateMediaFixture:
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user('final_media_owner')
        self.other = user.objects.create_user('final_media_other')
        self.staff = user.objects.create_superuser('final_media_staff', 'qa@example.invalid', 'synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner,
            with_subcategory=True, with_pricing_plan=True, with_schedule_days=True,
            status='draft', is_active=False, photo='', cover_photo='')
        self.storage = Place._meta.get_field('photo').storage

    def image(self, color='green'):
        buf = BytesIO()
        Image.new('RGB', (40, 40), color).save(buf, 'PNG')
        return buf.getvalue()

    def stored(self, name):
        return self.storage.save('places/' + name + '.png', ContentFile(self.image()))

    def propose(self, patch, submit=False):
        revision = VolunteerPlaceRevision.objects.filter(place=self.place).first()
        return publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch=patch, schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version, revision_version=revision.version if revision else 0,
            submit=submit)

    def form(self, changes=None, files=None):
        data = {'publication_token': publication_forms.version_token(self.place)}
        data.update(changes or {})
        return OwnerPlaceEditForm(data=data, files=files, instance=Place.objects.get(pk=self.place.pk),
            draft_save_only=True)

    def save(self, form, submit=False):
        self.assertTrue(form.is_valid(), form.errors)
        form.save(commit=False)
        return publication_forms.save_form(actor=self.owner, form=form, submit=submit)


class CandidateMediaTests(CandidateMediaFixture, TestCase):
    def test_saved_cover_survives_bound_draft_and_submission_and_approval(self):
        path = self.stored('cover')
        self.propose({'photo': path})
        revision = self.save(self.form())
        self.assertEqual(revision.payload.get('photo'), path)
        revision = self.save(self.form(), submit=True)
        self.assertEqual(revision.payload.get('photo'), path)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.photo.name, path)

    def test_candidate_photo_can_be_explicitly_cleared(self):
        self.propose({'photo': self.stored('clear-cover')})
        revision = self.save(self.form({'photo-clear': 'on'}))
        self.assertFalse(revision.payload.get('photo'))

    def test_new_upload_replaces_candidate_cover_without_changing_live(self):
        first = self.stored('old-cover')
        self.propose({'photo': first})
        revision = self.save(self.form(files={'photo': SimpleUploadedFile('replacement.png', self.image('red'), 'image/png')}))
        self.assertNotEqual(revision.payload.get('photo'), first)
        self.assertTrue(self.storage.exists(revision.payload['photo']))
        self.place.refresh_from_db()
        self.assertFalse(self.place.photo)

    def gallery(self, count=2):
        rows = [{'id': None, 'image': self.stored('gallery-' + str(n)), 'caption': '', 'order': n}
                for n in range(count)]
        self.propose({'gallery': rows})
        return rows

    def key(self, row):
        return 'candidate:' + hashlib.sha256(row['image'].encode()).hexdigest()

    def test_saved_candidate_gallery_reorders_and_keeps_keys_after_reload(self):
        rows = self.gallery()
        form = self.form({'gallery_order': json.dumps([self.key(rows[1]), self.key(rows[0])])})
        revision = self.save(form)
        self.assertEqual([r['image'] for r in sorted(revision.payload['gallery'], key=lambda r:r['order'])],
                         [rows[1]['image'], rows[0]['image']])
        loaded = OwnerPlaceEditForm(instance=self.place)
        self.assertEqual([r['key'] for r in loaded.saved_gallery_preview],
                         [self.key(rows[1]), self.key(rows[0])])
        self.assertEqual(self.place.gallery.count(), 0)

    def test_candidate_gallery_delete_add_and_approve_keeps_requested_order(self):
        rows = self.gallery()
        form = self.form({'delete_gallery_ids': [self.key(rows[0])],
                          'gallery_order': json.dumps(['new:0', self.key(rows[1])])},
                         files={'gallery_images': [SimpleUploadedFile('extra.png', self.image('blue'), 'image/png')]})
        revision = self.save(form, submit=True)
        self.assertEqual(len(revision.payload['gallery']), 2)
        self.assertNotIn(rows[0]['image'], [r['image'] for r in revision.payload['gallery']])
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.assertEqual(self.place.gallery.count(), 2)
        self.assertEqual(self.place.gallery.order_by('order').last().image.name, rows[1]['image'])

    def test_candidate_gallery_limit_counts_saved_files(self):
        self.gallery(10)
        form = self.form(files={'gallery_images': [SimpleUploadedFile('eleventh.png', self.image(), 'image/png')]})
        self.assertFalse(form.is_valid())
        self.assertIn('gallery_images', form.errors)

    def test_foreign_or_unknown_candidate_keys_cannot_delete_files(self):
        self.gallery()
        form = self.form({'delete_gallery_ids': ['candidate:' + 'f'*64]})
        self.assertFalse(form.is_valid())
        self.assertIn('delete_gallery_ids', form.errors)

    def test_stale_candidate_gallery_never_overwrites_current_order(self):
        rows = self.gallery()
        old_form = self.form({'gallery_order': json.dumps([self.key(rows[1]), self.key(rows[0])])})
        self.propose({'gallery': [rows[0]]})
        self.assertTrue(old_form.is_valid(), old_form.errors)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            publication_forms.save_form(actor=self.owner, form=old_form, submit=False)
        self.assertEqual(len(VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery']), 1)

    def test_gallery_editor_exposes_candidate_controls_without_fake_photo_ids(self):
        rows = self.gallery()
        self.client.force_login(self.owner)
        response = self.client.get(reverse('owner_place_edit', args=[self.place.pk]))
        self.assertContains(response, 'data-photo-saved="' + self.key(rows[0]) + '"')
        self.assertContains(response, 'value="' + self.key(rows[1]) + '"')
        self.assertNotContains(response, 'data-pc-saved-gallery')
        self.assertFalse(PlacePhoto.objects.filter(place=self.place).exists())


class AdminCandidateGalleryTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.url = reverse('admin:catalog_place_change', args=[self.place.pk])
        self.upload_name = self.stored('admin-candidate')
        for index in range(2):
            PlacePhoto.objects.create(place=self.place, image=self.stored('live-' + str(index)), order=index)
        self.propose({'gallery': [dict(id=None, image=self.upload_name, caption='QA saved candidate', order=0)]})

    def gallery_formset(self):
        response = self.client.get(self.url)
        return next(x.formset for x in response.context['inline_admin_formsets'] if x.formset.model is PlacePhoto)

    def test_admin_get_projects_saved_candidate_gallery_without_creating_live_rows(self):
        count = self.place.gallery.count()
        formset = self.gallery_formset()
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].instance.image.name, self.upload_name)
        self.assertIsNone(formset.forms[0].instance.pk)
        self.assertEqual(self.place.gallery.count(), count)

    def test_main_admin_adapter_does_not_reset_saved_gallery_before_inline_edit(self):
        from types import SimpleNamespace
        before = VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery']
        form = SimpleNamespace(instance=publication_forms.candidate_for_edit(self.place),
            data={'publication_token': publication_forms.version_token(self.place)}, cleaned_data={})
        publication_forms.save_form(actor=self.staff, form=form, submit=False)
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery'], before)

    def test_candidate_management_and_foreign_id_cannot_claim_live_photo(self):
        cls = type(self.gallery_formset())
        base = {'gallery-TOTAL_FORMS': '1', 'gallery-INITIAL_FORMS': '0',
                'gallery-MIN_NUM_FORMS': '0', 'gallery-MAX_NUM_FORMS': '10',
                'gallery-0-caption': 'QA tamper', 'gallery-0-order': '0'}
        foreign = create_quality_place()
        photo = PlacePhoto.objects.create(place=foreign, image=self.stored('foreign'))
        for patch in ({'gallery-0-id': str(photo.pk)}, {'gallery-INITIAL_FORMS': '1'}, {'gallery-TOTAL_FORMS': '0'}):
            with self.subTest(patch=patch):
                formset = cls(data={**base, **patch}, instance=self.place, prefix='gallery')
                self.assertFalse(formset.is_valid())
        self.assertEqual(self.place.gallery.count(), 2)
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery'][0]['caption'], 'QA saved candidate')

    def test_replacing_candidate_file_does_not_replace_live_file(self):
        from catalog.services.publication_forms import save_admin_related
        cls = type(self.gallery_formset())
        data = {'gallery-TOTAL_FORMS': '1', 'gallery-INITIAL_FORMS': '0',
                'gallery-MIN_NUM_FORMS': '0', 'gallery-MAX_NUM_FORMS': '10',
                'gallery-0-caption': 'QA replacement', 'gallery-0-order': '0'}
        formset = cls(data=data, files={'gallery-0-image': SimpleUploadedFile('replacement.png', self.image('red'), content_type='image/png')}, instance=self.place, prefix='gallery')
        self.assertTrue(formset.is_valid(), formset.errors)
        save_admin_related(actor=self.staff, place=self.place, formsets=[formset], uploads=[], submit=False)
        rows = VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery']
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]['image'], self.upload_name)
        self.assertEqual(self.place.gallery.count(), 2)

    def test_edit_saved_candidate_caption_then_delete_keeps_live_gallery(self):
        from catalog.services.publication_forms import save_admin_related
        cls = type(self.gallery_formset())
        data = {'gallery-TOTAL_FORMS': '1', 'gallery-INITIAL_FORMS': '0',
                'gallery-MIN_NUM_FORMS': '0', 'gallery-MAX_NUM_FORMS': '10',
                'gallery-0-caption': 'QA revised candidate', 'gallery-0-order': '0'}
        formset = cls(data=data, instance=self.place, prefix='gallery')
        self.assertTrue(formset.is_valid(), formset.errors)
        save_admin_related(actor=self.staff, place=self.place, formsets=[formset], uploads=[], submit=False)
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.payload['gallery'], [dict(id=None, image=self.upload_name, caption='QA revised candidate', order=0)])
        data['gallery-0-DELETE'] = 'on'
        formset = cls(data=data, instance=self.place, prefix='gallery')
        self.assertTrue(formset.is_valid(), formset.errors)
        save_admin_related(actor=self.staff, place=self.place, formsets=[formset], uploads=[], submit=False)
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['gallery'], [])
        self.assertEqual(self.place.gallery.count(), 2)


class LegacyReviewProjectionTests(CandidateMediaFixture, TestCase):
    # Keep these scenarios separate from media tests in test discovery.
    def test_review_projects_public_space_nature_before_contact_readiness(self):
        revision = self.propose({'nature': 'public_space', 'phone1': '', 'phone2': '', 'phone3': '', 'website': ''}, submit=True)
        form = review_form(revision)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.instance.nature, 'public_space')
        self.assertNotIn('missing_phone', evaluate_form_readiness(form, form.instance).quality_codes)

    def test_review_counts_group_only_price_and_can_approve(self):
        nested = {'pricing_schema_version': 2, 'activities': [{
            'name_az': 'Rəsm', 'description_az': 'Uşaqlar üçün rəsm dərsləri.',
            'groups': [{'name_az': 'Uşaqlar', 'age_from': 0, 'age_to': 12,
                        'schedule_text': 'Çərşənbə 15:00',
                        'pricing_plans': [{'product_type': 'lesson', 'price': '15'}]}]}]}
        revision = self.propose({'pricing_plans': [], 'nested_pricing': nested}, submit=True)
        form = review_form(revision)
        self.assertTrue(form.is_valid(), form.errors)
        readiness = evaluate_form_readiness(form, form.instance)
        self.assertTrue(readiness.is_ready, readiness.issues)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.assertEqual(self.place.activities.first().offering_groups.first().pricing_plan_records.first().price, 15)


class EventAdminVersionTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.staff = user.objects.create_superuser('final_event_staff', 'event@example.invalid', 'synthetic')
        self.owner = user.objects.create_user('final_event_owner')
        self.organization = Organization.objects.create(owner=self.owner, name_az='QA Final organization')
        start = timezone.now() + timedelta(days=20)
        self.event = Event.objects.create(name='QA Final event', name_az='QA Final event', category='EDU',
            organizer_organization=self.organization, organizer_resolution='resolved',
            event_format='online', start_datetime=start, end_datetime=start+timedelta(hours=1))
        self.client.force_login(self.staff)
        self.url = reverse('admin:catalog_event_change', args=[self.event.pk])

    def payload(self):
        data = existing_admin_tests.TestAdminOwnershipModerationUX._admin_event_change_payload(self, self.event)
        data.update(expected_updated_at=self.event.updated_at.isoformat(), _save_draft='1')
        return data

    def test_stale_admin_post_retains_input_and_does_not_write(self):
        data = self.payload()
        data['name_az'] = 'QA stale event input'
        Event.objects.filter(pk=self.event.pk).update(name_az='QA fresh event input', updated_at=timezone.now())
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['adminform'].form['name_az'].value(), data['name_az'])
        self.assertIn('stale_version', [e.code for e in response.context['adminform'].form.non_field_errors().as_data()])
        self.event.refresh_from_db()
        self.assertEqual(self.event.name_az, 'QA fresh event input')

    def test_change_without_original_version_refuses_write(self):
        data = self.payload()
        del data['expected_updated_at']
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.errors)

    def test_gallery_placeholder_only_exists_inside_template(self):
        from html.parser import HTMLParser
        class GalleryParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_template = False
                self.outside_names = []
            def handle_starttag(self, tag, attrs):
                if tag == 'template':
                    self.in_template = True
                name = dict(attrs).get('name', '')
                if tag == 'input' and '__prefix__' in name and not self.in_template:
                    self.outside_names.append(name)
            def handle_endtag(self, tag):
                if tag == 'template':
                    self.in_template = False
        parser = GalleryParser()
        parser.feed(self.client.get(self.url).content.decode())
        self.assertEqual(parser.outside_names, [])

    def test_fresh_admin_save_succeeds_and_template_has_one_token(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="expected_updated_at"', count=1)
        data = self.payload()
        data['name_az'] = 'QA valid event edit'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name_az, data['name_az'])


class SourceLanguageDisplayTests(TestCase):
    def test_event_description_uses_existing_source_without_creating_translations(self):
        event = Event(description_az='İlkin mətn')
        self.assertEqual(event.description_i18n('ru'), 'İlkin mətn')
        self.assertEqual(event.description_i18n('en'), 'İlkin mətn')
        self.assertEqual((event.description_ru, event.description_en), ('', ''))
        event.description_en = 'English version'
        self.assertEqual(event.description_i18n('en'), 'English version')

    def test_specialist_existing_ru_fallback_kept_and_other_source_not_lost(self):
        specialist = Specialist(bio_az='AZ bio', bio_ru='RU bio')
        self.assertEqual(specialist.bio_i18n('en'), 'RU bio')
        specialist.bio_ru = ''
        self.assertEqual(specialist.bio_i18n('en'), 'AZ bio')
        for field in ('education', 'experience_info'):
            setattr(specialist, field + '_az', 'AZ original')
            self.assertEqual(getattr(specialist, field + '_i18n')('ru'), 'AZ original')

    def test_fallback_marker_is_localized_and_text_is_escaped(self):
        from django.template.loader import render_to_string
        from django.utils.translation import override
        from catalog.services.localized_content import localized_content
        event = Event(description_az='<script>original</script>')
        with override('en'):
            content = localized_content(event, 'description')
            self.assertTrue(content['is_fallback'])
            html = render_to_string('catalog/includes/localized_content.html', {'content': content})
            self.assertIn('lang="az"', html)
            self.assertIn('AZ', html)
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)

class EventVenueMetadataTests(TestCase):
    def test_venue_metadata_uses_canonical_location_and_machine_numbers(self):
        from django.utils.translation import override
        owner = get_user_model().objects.create_user('venue_metadata_owner')
        Organization.objects.create(name_az='QA organizer', owner=owner)
        place = create_quality_place(owner=owner, status='published', is_active=True,
                                     district='baku_yasamal', lat=40.411, lng=49.822)
        self.client.force_login(owner)
        for language in ('ru', 'az', 'en'):
            with self.subTest(language=language), override(language):
                response = self.client.get(reverse('owner_event_create'))
                self.assertContains(response, 'data-region="baku"')
                self.assertContains(response, 'data-lat="40.411"')
                self.assertContains(response, 'data-lng="49.822"')
                self.assertContains(response, f'data-district="{place.district}"')
        # Legacy numeric zero must remain visible; do not relax save-time geography.
        Place.objects.filter(pk=place.pk).update(lat=0, lng=0)
        response = self.client.get(reverse('owner_event_create'))
        self.assertContains(response, 'data-lat="0.0"')
        Place.objects.filter(pk=place.pk).update(lat=None, lng=None)
        response = self.client.get(reverse('owner_event_create'))
        self.assertContains(response, 'data-lat=""')
        self.assertContains(response, 'data-lng=""')
        self.assertNotContains(response, 'data-lat="None"')

class SpecialistCatalogVenueTests(TestCase):
    def test_practice_at_kidsmap_place_localizes_string_district_without_500(self):
        from catalog.models import SiteSettings, SpecialistPracticeLocation
        from django.utils.translation import override
        site = SiteSettings.get_solo(); site.specialists_section_enabled = True; site.save()
        place = create_quality_place(district='baku_yasamal')
        specialist = Specialist.objects.create(name='QA catalog venue', status='published',
                                              consultation_format='offline')
        SpecialistPracticeLocation.objects.create(specialist=specialist, place=place, is_active=True)
        for language in ('ru', 'az', 'en'):
            with self.subTest(language=language), override(language):
                response = self.client.get(reverse('specialist_list'))
                self.assertContains(response, 'QA catalog venue')
                self.assertContains(response, place.district_i18n(language))


class EventAdminAutocommitTests(TransactionTestCase):
    setUp = EventAdminVersionTests.setUp

    def test_edit_get_readiness_does_not_lock_or_write_outside_transaction(self):
        from django.db import connection
        self.assertFalse(connection.in_atomic_block)
        before = self.event.updated_at
        response = self.client.get(self.url)
        self.assertContains(response, 'name="expected_updated_at"', count=1)
        self.event.refresh_from_db()
        self.assertEqual(self.event.updated_at, before)
