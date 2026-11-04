"""User-visible onboarding regressions: navigation and contact validation."""
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.translation import override

from catalog.forms import OwnerSpecialistForm
from catalog.models import SiteSettings, Specialist, SpecialistClaim, SpecialistProposalDraft, SpecialistSpecialization


class SpecialistOnboardingInputTests(TestCase):
    def setUp(self):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.spec = SpecialistSpecialization.objects.create(code='input-qa', name_ru='QA')

    def form(self, **changes):
        data = dict(name='Synthetic specialist', bio_ru='Biography', consultation_format='online',
                    phone='+994 50 123 45 67', language_ru='on', specializations=[self.spec.pk])
        data.update(changes)
        return OwnerSpecialistForm(data)

    def test_anonymous_entry_preserves_destination_through_login(self):
        user = get_user_model().objects.create_user('onboarding-login', password='SyntheticLogin2026!')
        destination = '/ru/account/places/specialists/create/?source=catalog'
        response = self.client.get(destination)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(parse_qs(urlsplit(response['Location']).query).get('next'), [destination])
        login = self.client.post(response['Location'], {'username': user.username, 'password': 'SyntheticLogin2026!', 'next': destination})
        self.assertRedirects(login, destination, fetch_redirect_response=False)

    def test_anonymous_resume_preserves_uuid(self):
        destination = '/ru/account/specialists/proposals/12345678-1234-1234-1234-123456789abc/'
        response = self.client.get(destination)
        self.assertEqual(parse_qs(urlsplit(response['Location']).query).get('next'), [destination])

    def test_invalid_contacts_are_rejected_even_with_valid_alternative(self):
        for field in ('phone', 'whatsapp'):
            for value in ('abc', '123', '+1234567890123456', '-------', '50<script>1234567'):
                with self.subTest(field=field, value=value):
                    form = self.form(**{field: value})
                    self.assertFalse(form.is_valid())
                    self.assertIn(field, form.errors)

    def test_supported_formatted_phone_numbers_and_whatsapp_only(self):
        for value in ('+994 50 123 45 67', '050 123 45 67', '+44 20 7946 0958', '+1 (202) 555-0123', '00994 50 123 45 67'):
            with self.subTest(value=value):
                form = self.form(phone=value)
                self.assertTrue(form.is_valid(), form.errors)
        form = self.form(phone='', whatsapp='+994 50 123 45 67')
        self.assertTrue(form.is_valid(), form.errors)

    def test_incomplete_contact_can_be_saved_as_draft(self):
        form = OwnerSpecialistForm({'phone': '+994 5'}, draft_save_only=True)
        self.assertTrue(form.is_valid(), form.errors)

    def test_group_requirements_have_one_error_each(self):
        with override('ru'):
            form = self.form(phone='', bio_ru='', language_ru='')
            self.assertFalse(form.is_valid())
            self.assertEqual(set(form.errors), {'bio_ru', 'language_az', 'phone'})

    def test_reopened_application_closed_by_moderator_is_not_a_server_error(self):
        actor = get_user_model().objects.create_user('stale-applicant')
        person = Specialist.objects.create(name='Changed by moderator', created_by=actor, status='published')
        draft = SpecialistProposalDraft.objects.create(pk=uuid4(), actor=actor, submitted_specialist=person, payload={})
        self.client.force_login(actor)
        url = f'/ru/account/specialists/proposals/{draft.pk}/'
        for method in (self.client.get, self.client.post):
            response = method(url)
            self.assertRedirects(response, '/ru/account/specialists/', fetch_redirect_response=False)
        person.refresh_from_db()
        self.assertEqual(person.status, 'published')

    def test_returned_application_has_one_working_card_not_a_second_submitted_card(self):
        actor = get_user_model().objects.create_user('returned-index')
        person = Specialist.objects.create(name='Returned profile', created_by=actor, status='draft')
        SpecialistProposalDraft.objects.create(actor=actor, submitted_specialist=person, payload={'name': ['Returned profile']})
        SpecialistClaim.objects.create(applicant=actor, specialist=person, status='pending')
        self.client.force_login(actor)
        page = self.client.get('/ru/account/specialists/')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.context['working_proposals']), 1)
        self.assertEqual(page.context['claims'], [])
        self.assertFalse(page.context['proposals'])


class SpecialistPlaceLocationInputTests(TestCase):
    def test_place_text_geography_does_not_break_optional_location_relations(self):
        from unittest.mock import patch
        from catalog.forms_specialist_locations import PracticeLocationForm
        from catalog.models import Place, Region, District, MetroStation, SpecialistPracticeLocation
        actor = get_user_model().objects.create_user('place-location-applicant')
        region = Region.objects.create(key='input-region', name_ru='Region')
        district = District.objects.create(key='input-district', region=region, name_ru='District')
        metro = MetroStation.objects.create(key='input-metro', name_ru='Metro')
        from catalog.testcases.utils import create_quality_place
        place = create_quality_place(name='Synthetic centre', address='Synthetic address',
                                     district='baku', metro='28-may', lat=40.4, lng=49.8)
        for selected in (False, True):
            with self.subTest(selected_geography=selected), patch(
                'catalog.forms_specialist_locations.visible_practice_places',
                return_value=Place.objects.filter(pk=place.pk),
            ):
                form = PracticeLocationForm(
                    {'place':place.pk, 'region':region.pk, 'is_active':'on',
                     'district':district.pk if selected else '', 'metro':metro.pk if selected else ''},
                    actor=actor,
                    instance=SpecialistPracticeLocation(specialist=Specialist(consultation_format='offline')),
                )
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data['address'], place.address)
                self.assertEqual((form.cleaned_data['lat'], form.cleaned_data['lng']), (40.4,49.8))
                self.assertEqual(form.cleaned_data['region'], region)
                self.assertEqual(form.cleaned_data['district'], district if selected else None)
                self.assertEqual(form.cleaned_data['metro'], metro if selected else None)
