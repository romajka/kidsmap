"""Category-based contact requirements without an owner-controlled nature flag."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.models import Category, Place, Subcategory, VolunteerPlaceRevision
from catalog.services.content_quality import public_place_queryset, place_catalog_visibility_reasons
from catalog.services.place_readiness import evaluate_place_readiness
from catalog.testcases.utils import create_ready_place, ensure_quality_subcategory


class PlaceContactPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parks, _ = Category.objects.get_or_create(code='parks-playgrounds', defaults={'name': 'Парки и площадки'})
        cls.park, _ = Subcategory.objects.get_or_create(category=cls.parks, code='parks-boulevards', defaults={'name': 'Парки и бульвары'})
        cls.playground, _ = Subcategory.objects.get_or_create(category=cls.parks, code='playgrounds', defaults={'name': 'Детские площадки'})
        cls.botanical, _ = Subcategory.objects.get_or_create(category=cls.parks, code='botanical-gardens', defaults={'name': 'Ботанические сады'})
        cls.education = ensure_quality_subcategory('EDU')
        cls.owner = get_user_model().objects.create_user('contact_policy_owner', email='contact-owner@example.invalid')
        cls.reviewer = get_user_model().objects.create_superuser('contact_policy_reviewer', email='contact-reviewer@example.invalid')

    def payload(self, **changes):
        data = dict(name_az='Ailə gəzinti məkanı', description_az='Ailələr və uşaqlar üçün rahat gəzinti yeri.',
                    category=self.parks.pk, subcategory=str(self.park.pk), age_from='0', age_to='18',
                    region='baku', district='baku_yasamal', address='Bakı, parkın əsas girişi', lat='40.4', lng='49.8',
                    schedule_mode='always_open', phone1='', phone2='', phone3='', website='',
                    pricing_plans=json.dumps([{'product_type': 'admission', 'price_kind': 'free'}]))
        data.update(changes)
        return data

    def test_parks_and_playgrounds_are_fully_ready_and_visible_without_contacts(self):
        for sub in (self.park, self.playground):
            with self.subTest(subcategory=sub.code):
                place = create_ready_place(category=self.parks, subcategory=sub, phone1='', phone2='', phone3='', website='', instagram='')
                readiness = evaluate_place_readiness(place)
                self.assertTrue(readiness.is_ready, readiness.issues)
                self.assertEqual(readiness.percentage, 100)
                self.assertTrue(public_place_queryset(Place.objects.all()).filter(pk=place.pk).exists())
                self.assertNotIn('missing_contact', place_catalog_visibility_reasons(place))

    def test_owner_form_accepts_park_without_nature_or_contacts(self):
        form = OwnerPlaceCreateForm(data=self.payload())
        self.assertNotIn('nature', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        contact = next(item for item in form.submission_readiness['items'] if item['code'] == 'phone')
        self.assertTrue(contact['complete'])
        pairs = contact['config']['optional_pairs']
        self.assertIn(str(self.park.pk), pairs[self.parks.pk])

    def test_commercial_and_ambiguous_subcategories_still_need_a_contact(self):
        for category, sub in ((self.education.category_id, self.education), (self.parks.pk, self.botanical)):
            with self.subTest(subcategory=sub.code):
                form = OwnerPlaceCreateForm(data=self.payload(category=category, subcategory=str(sub.pk), nature='public_space'))
                self.assertFalse(form.is_valid())
                self.assertIn('phone1', form.errors)
                allowed = OwnerPlaceCreateForm(data=self.payload(category=category, subcategory=str(sub.pk), website='https://example.invalid'))
                self.assertTrue(allowed.is_valid(), allowed.errors)

    def test_wrong_parent_or_similarly_named_subcategory_does_not_exempt(self):
        Subcategory.objects.filter(pk=self.playground.pk).update(category=self.education.category)
        wrong = Subcategory.objects.get(pk=self.playground.pk)
        for category, sub in ((self.education.category_id, wrong), (self.parks.pk, wrong)):
            form = OwnerPlaceCreateForm(data=self.payload(category=category, subcategory=str(sub.pk)))
            self.assertFalse(form.is_valid())
            self.assertIn('phone1', form.errors)
        place = create_ready_place(category=self.education.category, subcategory=wrong, phone1='')
        self.assertFalse(public_place_queryset(Place.objects.all()).filter(pk=place.pk).exists())
        mismatched = create_ready_place(category=self.parks, subcategory=wrong, phone1='')
        self.assertFalse(public_place_queryset(Place.objects.all()).filter(pk=mismatched.pk).exists())
        self.assertIn('phone', [item.code for item in evaluate_place_readiness(mismatched).issues])

    def test_contact_is_validated_even_when_optional(self):
        form = OwnerPlaceCreateForm(data=self.payload(phone1='not-a-phone'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone1', form.errors)

    def test_changing_public_place_to_centre_does_not_inherit_contact_exception(self):
        place = create_ready_place(category=self.parks, subcategory=self.park, owner=self.owner, phone1='')
        Place.objects.filter(pk=place.pk).update(nature='public_space', nature_approved_at=timezone.now())
        place.refresh_from_db()
        from catalog.services.publication_forms import version_token
        form = OwnerPlaceEditForm(instance=place, submit_for_moderation=True, data=self.payload(
            category=self.education.category_id, subcategory=str(self.education.pk), lat='', lng='', publication_token=version_token(place)))
        self.assertFalse(form.is_valid())
        self.assertIn('phone1', form.errors)
        contact = next(item for item in form.submission_readiness['items'] if item['code'] == 'phone')
        self.assertFalse(contact['complete'])
        self.assertEqual(contact['config']['original_category'], self.parks.pk)
        self.assertEqual(Place.objects.get(pk=place.pk).nature, 'public_space')

    def test_existing_public_space_exception_is_preserved_without_type_control(self):
        place = create_ready_place(owner=self.owner, phone1='')
        Place.objects.filter(pk=place.pk).update(nature='public_space', nature_approved_at=timezone.now())
        place.refresh_from_db()
        form = OwnerPlaceEditForm(instance=place)
        self.assertNotIn('nature', form.fields)
        contact = next(item for item in form.submission_readiness['items'] if item['code'] == 'phone')
        self.assertTrue(contact['complete'])

    def test_owner_submit_then_moderator_approval_exposes_contactless_park(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('owner_place_create') + '?type=permanent')
        self.assertNotContains(response, 'name="nature"')
        response = self.client.post(reverse('owner_place_create'), self.payload(form_action='save_and_publish', create_separate='1'))
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else '')
        revision = VolunteerPlaceRevision.objects.get(author=self.owner, status='pending')
        place = revision.place
        original_nature = place.nature
        self.assertNotIn('nature', revision.payload)
        self.assertFalse(public_place_queryset(Place.objects.all()).filter(pk=place.pk).exists())
        from catalog.services import publication
        publication.review(actor=self.reviewer, revision_id=revision.pk, version=revision.version, approve=True)
        place.refresh_from_db()
        self.assertEqual(place.nature, original_nature)
        self.assertTrue(evaluate_place_readiness(place).is_ready)
        self.assertTrue(public_place_queryset(Place.objects.all()).filter(pk=place.pk).exists())

    def test_legacy_public_park_is_exempt_but_other_park_names_are_not(self):
        from catalog.services.contact_policy import contact_optional
        self.assertTrue(contact_optional(category_code='PARK', subcategory_code='public-parks', subcategory_category_code='PARK'))
        for code in ('amusement-parks', 'rope-parks', 'botanical-gardens', 'national-parks', 'beaches-beach-clubs', ''):
            with self.subTest(code=code):
                self.assertFalse(contact_optional(category_code='parks-playgrounds', subcategory_code=code, subcategory_category_code='parks-playgrounds'))

    def test_unbound_commercial_form_has_contact_required_hint_without_javascript(self):
        self.client.force_login(self.owner)
        from django.utils.translation import override
        with override('ru'):
            response = self.client.get('/ru/account/places/create/?type=permanent')
        self.assertContains(response, 'data-pc-contact-hint aria-live="polite">Укажите телефон, WhatsApp или сайт.')

    def test_reopening_candidate_taxonomy_uses_live_taxonomy_for_legacy_exception(self):
        place = create_ready_place(category=self.parks, subcategory=self.park, phone1='')
        Place.objects.filter(pk=place.pk).update(nature='public_space', nature_approved_at=timezone.now())
        place.refresh_from_db()
        VolunteerPlaceRevision.objects.create(place=place, author=self.owner, payload={
            'category': self.education.category_id, 'subcategory': self.education.pk})
        form = OwnerPlaceEditForm(instance=place)
        contact = next(item for item in form.submission_readiness['items'] if item['code'] == 'phone')
        self.assertFalse(contact['complete'])
        self.assertEqual(contact['config']['original_category'], self.parks.pk)
        self.assertEqual(Place.objects.get(pk=place.pk).category_id, self.parks.pk)

    def test_unapproved_candidate_nature_cannot_remove_contact_requirement(self):
        place = create_ready_place(phone1='')
        VolunteerPlaceRevision.objects.create(place=place, author=self.owner, payload={'nature': 'public_space'})
        form = OwnerPlaceEditForm(instance=place)
        contact = next(item for item in form.submission_readiness['items'] if item['code'] == 'phone')
        self.assertFalse(contact['complete'])
        self.assertFalse(contact['config']['optional'])
