"""Stage25 public person boundaries and legacy URLs on isolated synthetic records."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Organization, SiteSettings, Specialist, SpecialistPracticeLocation
from catalog.services import specialist_domain


class SpecialistPublicScreensTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user('screens-person')
        self.owner = users.objects.create_user('screens-org-owner')
        self.profile = Specialist.objects.create(name='Synthetic shared name', slug='screens-legacy-url',
            status='published', is_active=True, consultation_format='online',
            verified_person_user=self.person, person_verified_at=timezone.now())
        self.org = Organization.objects.create(name_az='Synthetic current organization',
            owner=self.owner, status='published', approved_at=timezone.now())
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def link(self, role, start, end=None):
        link = specialist_domain.propose_employment(actor=self.owner, specialist_id=self.profile.pk,
            organization_id=self.org.pk, role=role, start_date=start, end_date=end)
        specialist_domain.confirm_employment(actor=self.person, employment_id=link.pk,
            side='person', expected_version=1)
        specialist_domain.confirm_employment(actor=self.owner, employment_id=link.pk,
            side='organization', expected_version=2)
        link.refresh_from_db()
        return link

    def test_date_state_and_stale_owner_consent_are_never_current_work(self):
        from catalog.services.specialist_presentation import public_profile_context
        today = timezone.localdate()
        live = self.link('Current teacher', today - timedelta(days=1))
        past = self.link('Past teacher', today - timedelta(days=50), today - timedelta(days=2))
        future = self.link('Future teacher', today + timedelta(days=1))
        cancelled = self.link('Cancelled teacher', today - timedelta(days=1))
        specialist_domain.cancel_employment(actor=self.person, employment_id=cancelled.pk,
            expected_version=cancelled.version)
        context = public_profile_context(self.profile)
        self.assertEqual([x.pk for x in context['specialist_current_employment']], [live.pk])
        self.assertEqual({x.pk for x in context['specialist_past_employment']}, {past.pk, cancelled.pk})
        self.assertEqual([x.pk for x in context['specialist_future_employment']], [future.pk])
        Organization.objects.filter(pk=self.org.pk).update(ownership_version=self.org.ownership_version + 1)
        context = public_profile_context(self.profile)
        self.assertFalse(context['specialist_current_employment'])
        self.assertFalse(context['specialist_future_employment'])

    def test_unconfirmed_relationship_and_unpublished_organization_not_public(self):
        from catalog.services.specialist_presentation import public_profile_context
        pending = specialist_domain.propose_employment(actor=self.owner, specialist_id=self.profile.pk,
            organization_id=self.org.pk, role='Unconfirmed', start_date=timezone.localdate())
        specialist_domain.confirm_employment(actor=self.owner, employment_id=pending.pk,
            side='organization', expected_version=1)
        self.link('Hidden organization teacher', timezone.localdate())
        Organization.objects.filter(pk=self.org.pk).update(status='draft')
        context = public_profile_context(self.profile)
        for key in ('specialist_current_employment', 'specialist_past_employment', 'specialist_future_employment'):
            self.assertFalse(context[key])

    def test_all_old_locale_urls_200_and_retired_private_address_hidden(self):
        SpecialistPracticeLocation.objects.create(specialist=self.profile,
            address='SYNTHETIC RETIRED PRIVATE ADDRESS', is_active=False)
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang):
                legacy_url = '/%s/specialists/%s/' % (lang, self.profile.slug)
                if lang == 'az':
                    canonical = '/specialists/%s/' % self.profile.slug
                    legacy_response = self.client.get(legacy_url)
                    self.assertEqual(legacy_response.status_code, 301)
                    self.assertEqual(legacy_response['Location'], canonical)
                    response = self.client.get(canonical)
                else:
                    response = self.client.get(legacy_url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'SYNTHETIC RETIRED PRIVATE ADDRESS')
                self.assertIn('specialist_current_employment', response.context)
                self.assertEqual(response.context['practice_history'], [])

    def test_duplicate_name_profiles_are_distinct_and_no_claim_inferred(self):
        from catalog.services.specialist_presentation import public_profile_context
        other = Specialist.objects.create(name=self.profile.name, slug='screens-same-name',
            owner=self.owner, status='published', is_active=True)
        self.link('Confirmed teacher', timezone.localdate())
        context = public_profile_context(other)
        self.assertFalse(context['specialist_current_employment'])
        other.refresh_from_db()
        self.assertIsNone(other.verified_person_user_id)
        self.assertFalse(other.person_claims.exists())
        self.assertFalse(other.employment_links.exists())
