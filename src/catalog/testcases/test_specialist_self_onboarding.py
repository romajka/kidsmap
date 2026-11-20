"""A self application requests identity review; it never grants person access."""
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone

from catalog.models import SiteSettings, Specialist, SpecialistClaim, SpecialistSpecialization, UserProfile
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
        for path in ('/ru/account/specialists/',
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

    def test_add_specialist_route_opens_standalone_editor_and_defaults_to_self(self):
        response = self.client.get('/ru/account/places/specialists/create/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="account-nav-sidebar')
        self.assertContains(response, 'href="/ru/account/"')
        self.assertContains(response, '<input type="hidden" name="profile_subject" value="self">', html=True)
        self.assertNotContains(response, 'type="radio" name="profile_subject"')

    def set_account_details(self, phone='(050) 123-45-67'):
        self.actor.first_name = 'Synthetic'
        self.actor.last_name = 'Applicant'
        self.actor.save(update_fields=['first_name', 'last_name'])
        UserProfile.objects.update_or_create(user=self.actor, defaults={'phone': phone})

    def test_first_editor_suggests_own_name_and_keeps_phone_private(self):
        self.set_account_details()
        page = self.client.get('/ru/account/places/specialists/create/', follow=True)
        form = page.context['form']
        self.assertEqual(form['name'].value(), 'Synthetic Applicant')
        self.assertFalse(form['phone'].value())
        self.assertFalse(form['whatsapp'].value())
        self.assertEqual(page.context.get('account_phone_for_public_profile'), '+994501234567')

    def test_reopening_drafts_preserves_silent_or_edited_fields_and_all_work_formats(self):
        self.set_account_details()
        for selected_format, expected_codes, name in (
            ('online', ['online'], ''), ('offline', ['office'], 'Edited name'),
            ('both', ['online', 'office'], 'Second name'),
        ):
            with self.subTest(selected_format=selected_format):
                draft = self.save(self.data(name=name, consultation_format=selected_format, phone=''))
                page = self.client.get(f'/ru/account/specialists/proposals/{draft.pk}/')
                form = page.context['form']
                self.assertEqual(form['name'].value(), name)
                self.assertEqual(form['consultation_format'].value(), selected_format)
                self.assertEqual(form['session_formats'].value(), expected_codes)
                self.assertFalse(form['phone'].value())
                self.assertEqual(page.context.get('account_phone_for_public_profile'), '+994501234567')

    def test_other_and_legacy_drafts_never_offer_account_contacts(self):
        self.set_account_details()
        for subject in ('other', None):
            with self.subTest(subject=subject):
                data = self.data(subject=subject, name='Someone else', phone='')
                if subject is None:
                    del data['profile_subject']
                draft = self.save(data)
                url = f'/ru/account/specialists/proposals/{draft.pk}/'
                page = self.client.get(url)
                self.assertEqual(page.context['form']['name'].value(), 'Someone else')
                self.assertFalse(page.context.get('account_phone_for_public_profile'))
                # A resumed draft keeps its subject even after a stale or edited form POST.
                page = self.client.post(url, {**data.dict(), 'profile_subject':'self',
                                              'draft_key':str(draft.pk), 'draft_version':str(draft.version),
                                              'form_action':'save_draft'}, follow=True)
                self.assertEqual(page.context['profile_subject'], 'other')
                self.assertFalse(page.context.get('account_phone_for_public_profile'))

    def test_manual_phone_takes_precedence_and_invalid_account_contacts_are_never_offered(self):
        self.set_account_details()
        draft = self.save(self.data(phone='+994 55 123 45 67'))
        url = f'/ru/account/specialists/proposals/{draft.pk}/'
        page = self.client.get(url)
        self.assertEqual(page.context['form']['phone'].value(), '+994 55 123 45 67')
        self.assertFalse(page.context.get('account_phone_for_public_profile'))
        self.assertEqual(self.client.get('/ru/account/specialists/proposals/new/').context.get(
            'account_phone_for_public_profile'), '+994501234567')
        for account_phone in ('', 'старый контакт', '1234'):
            with self.subTest(account_phone=account_phone):
                self.set_account_details(account_phone)
                page = self.client.get('/ru/account/specialists/proposals/new/')
                self.assertFalse(page.context.get('account_phone_for_public_profile'))

    def test_missing_account_names_never_expose_login_or_email(self):
        self.actor.email = 'private@example.test'
        self.actor.save(update_fields=['email'])
        page = self.client.get('/ru/account/specialists/proposals/new/')
        self.assertFalse(page.context['form']['name'].value())
        self.assertFalse(page.context.get('account_phone_for_public_profile'))

    def test_stale_new_tab_keeps_existing_proposal_subject_and_manual_name_on_error(self):
        self.set_account_details()
        draft = self.save(self.data(subject='other', name='Original name', phone=''))
        page = self.client.post('/ru/account/specialists/proposals/new/', {
            **self.data(name='Manual correction', phone='').dict(),
            'draft_key': str(draft.pk), 'draft_version': '0', 'form_action': 'save_draft',
        })
        self.assertEqual(page.status_code, 409)
        self.assertEqual(page.context['form']['name'].value(), 'Manual correction')
        self.assertEqual(page.context['profile_subject'], 'other')
        self.assertFalse(page.context.get('account_phone_for_public_profile'))

    def test_whatsapp_only_submit_does_not_copy_private_phone(self):
        self.set_account_details()
        draft = self.save(self.data(phone='', whatsapp='+994 55 123 45 67'), submit=True)
        self.assertFalse(draft.submitted_specialist.phone)
        self.assertEqual(draft.submitted_specialist.whatsapp, '+994551234567')

    def test_entry_resumes_a_single_self_draft_and_keeps_explicit_new_entry(self):
        foreign = get_user_model().objects.create_user('other-applicant')
        save_proposal(actor=foreign, draft_id=uuid4(), expected_version='0', data=self.data(), files={})
        self.save(self.data(subject='other'))
        entry = '/ru/account/places/specialists/create/'
        new = '/ru/account/specialists/proposals/new/'
        self.assertRedirects(self.client.get(entry), new, fetch_redirect_response=False)
        draft = self.save(self.data(name='Continue this draft'))
        page = self.client.get(entry, follow=True)
        self.assertEqual(page.redirect_chain, [(f'/ru/account/specialists/proposals/{draft.pk}/', 302)])
        self.assertEqual(page.context['form']['name'].value(), 'Continue this draft')
        self.assertRedirects(self.client.get(entry + '?fresh=1'), new, fetch_redirect_response=False)
        self.assertIsNone(self.client.get(new).context['proposal_draft'])

    def test_entry_offers_a_choice_if_several_self_drafts_exist(self):
        drafts = [self.save(self.data(name=name)) for name in ('First draft', 'Second draft')]
        page = self.client.get('/ru/account/places/specialists/create/', follow=True)
        self.assertEqual(page.redirect_chain, [('/ru/account/specialists/', 302)])
        for draft in drafts:
            self.assertContains(page, f'href="/ru/account/specialists/proposals/{draft.pk}/"')
        for locale, label in (('ru', 'Начать новую анкету'), ('az', 'Yeni anketə başla'), ('en', 'Start a new application')):
            prefix = '' if locale == 'az' else f'/{locale}'
            page = self.client.get(f'{prefix}/account/specialists/')
            self.assertContains(page, f'href="{prefix}/account/specialists/proposals/new/"')
            self.assertContains(page, label)

    def test_entry_reports_pending_application_and_resumes_returned_corrections(self):
        sent = self.save(self.data(), submit=True)
        entry = '/ru/account/places/specialists/create/'
        index = '/ru/account/specialists/'
        page = self.client.get(entry, follow=True)
        self.assertEqual(page.redirect_chain, [(index, 302)])
        self.assertContains(page, 'О решении модератора')
        self.assertContains(page, 'Подтверждение личности')
        self.assertContains(page, 'От вас пока ничего не требуется.')
        self.assertContains(page, 'Анкета ожидает проверки')
        self.assertContains(page, 'Ожидает решения модератора')
        self.assertNotContains(page, 'sw-application-documents')
        self.assertNotContains(page, 'data-step="4"')
        person = sent.submitted_specialist
        person.status = Specialist.STATUS_DRAFT
        person.rejection_reason = 'Уточните предмет'
        person.save(update_fields=['status','rejection_reason'])
        from catalog.services.specialist_moderation import reopen_author_draft
        reopened = reopen_author_draft(person)
        page = self.client.get(entry, follow=True)
        self.assertEqual(page.redirect_chain, [(f'/ru/account/specialists/proposals/{reopened.pk}/', 302)])
        self.assertContains(page, 'Уточните предмет')

    def test_rejected_identity_does_not_tell_the_applicant_to_wait(self):
        sent = self.save(self.data(), submit=True)
        claim = SpecialistClaim.objects.get(specialist=sent.submitted_specialist, applicant=self.actor)
        claim.status = SpecialistClaim.REJECTED
        claim.reason = 'Уточните фамилию в запросе.'
        claim.save(update_fields=['status', 'reason'])
        page = self.client.get('/ru/account/specialists/')
        self.assertContains(page, claim.reason)
        self.assertContains(page, f'/ru/account/specialists/{claim.specialist_id}/claims/')
        self.assertNotContains(page, 'От вас пока ничего не требуется.')

    def test_pending_clocks_use_separate_submission_and_claim_dates(self):
        from datetime import timedelta
        from catalog.models import SpecialistProposalDraft

        draft = self.save(self.data(), submit=True)
        claim = SpecialistClaim.objects.get(specialist=draft.submitted_specialist, applicant=self.actor)
        submitted = timezone.now().replace(microsecond=0) - timedelta(days=2)
        claimed = submitted + timedelta(hours=3)
        SpecialistProposalDraft.objects.filter(pk=draft.pk).update(submitted_at=submitted)
        SpecialistClaim.objects.filter(pk=claim.pk).update(created_at=claimed)
        url = f'/ru/account/specialists/{claim.specialist_id}/claims/'

        self.assertContains(self.client.get('/ru/account/specialists/'), f'datetime="{timezone.localtime(submitted).isoformat()}"')
        self.assertContains(self.client.get(url), f'datetime="{timezone.localtime(claimed).isoformat()}"')
        self.assertContains(self.client.get(url), 'data-wait-elapsed')
        self.client.post(url, {'action': 'withdraw', 'claim_id': claim.pk, 'expected_version': claim.version})
        page = self.client.get(url)
        self.assertNotContains(page, 'data-wait-elapsed')
        self.assertContains(page, 'Запрос отозван')

    def test_entry_takes_confirmed_owner_to_management_even_with_an_old_draft(self):
        self.save(self.data())
        person = Specialist.objects.create(name='Confirmed person', verified_person_user=self.actor,
                                            person_verified_at=timezone.now(), status='published', is_active=True)
        page = self.client.get('/ru/account/places/specialists/create/', follow=True)
        self.assertEqual(page.redirect_chain, [('/ru/account/specialists/', 302)])
        self.assertContains(page, f'href="/ru/account/specialists/{person.pk}/"')
        self.assertNotContains(page, 'Начать новую анкету')

    def test_confirmed_profile_editor_uses_full_page_with_return_to_account(self):
        profile = Specialist.objects.create(name='Synthetic confirmed person', verified_person_user=self.actor,
                                            person_verified_at=timezone.now(), consultation_format='online')
        response = self.client.get(f'/ru/account/specialists/{profile.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="account-nav-sidebar')
        self.assertNotContains(response, 'class="account-user-card')
        self.assertContains(response, 'href="/ru/account/"')
        self.assertContains(response, 'id="specialist-create-form"')

    def test_self_draft_resumes_and_is_visible_without_requesting_identity_yet(self):
        draft = self.save(self.data())
        self.assertEqual(draft.payload.get('profile_subject'), ['self'])
        self.assertFalse(SpecialistClaim.objects.exists())
        self.assertFalse(Specialist.objects.exists())
        page = self.client.get(f'/ru/account/specialists/proposals/{draft.pk}/')
        self.assertContains(page, '<input type="hidden" name="profile_subject" value="self">', html=True)
        account = self.client.get('/ru/account/')
        self.assertContains(account, 'href="/ru/account/specialists/"')
        index = self.client.get('/ru/account/specialists/')
        self.assertContains(index, str(draft.pk))
        self.assertNotContains(index, '<h1>Кабинет специалиста</h1>')

    def test_existing_other_draft_retains_its_subject_when_resumed(self):
        draft = self.save(self.data(subject='other'))
        page = self.client.get(f'/ru/account/specialists/proposals/{draft.pk}/')
        self.assertContains(page, '<input type="hidden" name="profile_subject" value="other">', html=True)
        self.assertNotContains(page, 'type="radio" name="profile_subject"')

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
