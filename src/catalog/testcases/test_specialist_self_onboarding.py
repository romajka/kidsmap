"""A self application requests identity review; it never grants person access."""
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone

from catalog.models import SiteSettings, Specialist, SpecialistClaim, SpecialistSpecialization
from catalog.services import specialist_domain
from catalog.services.specialist_proposal_drafts import save_proposal


class SpecialistSelfOnboardingTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user('self-applicant')
        self.client.force_login(self.actor)
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.spec = SpecialistSpecialization.objects.create(code='self-qa', name_az='QA', name_ru='QA', name_en='QA')

    def data(self, subject='self', **extra):
        data = QueryDict('', mutable=True)
        data.update({'profile_subject': subject, 'name': 'Synthetic applicant',
                     'consultation_format': 'online', 'bio_ru': 'Synthetic biography',
                     'phone': '+994500000000', 'language_ru': 'on', 'specializations': str(self.spec.pk),
                     'locations-TOTAL_FORMS': '0', 'locations-INITIAL_FORMS': '0',
                     'locations-MIN_NUM_FORMS': '0', 'locations-MAX_NUM_FORMS': '30'})
        data.update(extra)
        return data

    def save(self, data, *, key=None, version=0, submit=False):
        return save_proposal(actor=self.actor, draft_id=key or uuid4(), expected_version=str(version),
                             data=data, files={}, submit=submit)

    def test_empty_account_has_add_action_and_no_empty_specialist_workspace(self):
        page = self.client.get('/ru/account/')
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'href="/ru/account/specialists/"')
        self.assertContains(page, 'href="/ru/account/places/specialists/create/"')
        self.assertRedirects(self.client.get('/ru/account/specialists/'), '/ru/account/', fetch_redirect_response=False)

    def test_specialist_pages_keep_account_identity_and_navigation(self):
        profile = Specialist.objects.create(name='Synthetic confirmed person', verified_person_user=self.actor,
                                            person_verified_at=timezone.now(), consultation_format='online')
        for path in ('/ru/account/specialists/', f'/ru/account/specialists/{profile.pk}/',
                     f'/ru/account/specialists/{profile.pk}/certificates/',
                     f'/ru/account/specialists/{profile.pk}/invitations/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['has_verified_specialist_profile'])
                self.assertContains(response, 'class="account-page-wrapper')
                self.assertContains(response, 'class="account-user-card')
                self.assertContains(response, 'class="account-nav-sidebar')
                self.assertContains(response, 'href="/ru/account/places/reviews/"')
                self.assertContains(response, 'href="/ru/account/settings/"')

    def test_add_specialist_route_keeps_account_frame_and_explicit_subject_choice(self):
        response = self.client.get('/ru/account/places/specialists/create/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="account-nav-sidebar')
        self.assertContains(response, 'value="self" checked')
        self.assertContains(response, 'value="other"')
        self.assertContains(response, 'Чей профиль вы добавляете?')

    def test_self_draft_resumes_and_is_visible_without_requesting_identity_yet(self):
        draft = self.save(self.data())
        self.assertEqual(draft.payload.get('profile_subject'), ['self'])
        self.assertFalse(SpecialistClaim.objects.exists())
        self.assertFalse(Specialist.objects.exists())
        page = self.client.get(f'/ru/account/specialists/proposals/{draft.pk}/')
        self.assertContains(page, 'value="self" checked')
        account = self.client.get('/ru/account/')
        self.assertContains(account, 'href="/ru/account/specialists/"')
        index = self.client.get('/ru/account/specialists/')
        self.assertContains(index, str(draft.pk))
        self.assertNotContains(index, '<h1>Кабинет специалиста</h1>')

    def test_self_submit_requests_review_once_and_does_not_grant_management(self):
        key = uuid4()
        sent = self.save(self.data(), key=key, submit=True)
        self.save(self.data(), key=key, submit=True)
        claim = SpecialistClaim.objects.get(specialist=sent.submitted_specialist, applicant=self.actor)
        self.assertEqual(claim.status, 'pending')
        profile = sent.submitted_specialist
        self.assertIsNone(profile.verified_person_user_id)
        self.assertIsNone(profile.owner_id)
        self.assertEqual(profile.status, 'pending')
        self.assertEqual(Specialist.objects.count(), 1)
        for suffix in ('', 'certificates/'):
            self.assertEqual(self.client.get(f'/ru/account/specialists/{profile.pk}/{suffix}').status_code, 404)
        index = self.client.get('/ru/account/specialists/')
        self.assertContains(index, profile.name)
        self.assertContains(index, 'Подтверждение личности')

    def test_other_and_legacy_proposals_do_not_request_identity(self):
        for subject in ('other', None):
            data = self.data(subject or 'other')
            if subject is None:
                del data['profile_subject']
            self.save(data, submit=True)
        self.assertFalse(SpecialistClaim.objects.exists())

    def test_reviewer_approval_unlocks_workspace_but_rejection_does_not(self):
        sent = self.save(self.data(), submit=True)
        claim = SpecialistClaim.objects.get(specialist=sent.submitted_specialist)
        reviewer = get_user_model().objects.create_user('self-reviewer', is_staff=True)
        reviewer.user_permissions.add(Permission.objects.get(codename='review_specialist_claim'))
        specialist_domain.review_claim(actor=reviewer, claim_id=claim.pk, expected_version=claim.version,
                                       approve=False, reason='Synthetic reason')
        self.assertEqual(self.client.get(f'/ru/account/specialists/{claim.specialist_id}/').status_code, 404)
        claim = specialist_domain.request_claim(actor=self.actor, specialist_id=claim.specialist_id)
        specialist_domain.review_claim(actor=reviewer, claim_id=claim.pk, expected_version=claim.version, approve=True)
        self.assertEqual(self.client.get(f'/ru/account/specialists/{claim.specialist_id}/').status_code, 200)
        self.assertContains(self.client.get('/ru/account/'), 'Кабинет специалиста')
