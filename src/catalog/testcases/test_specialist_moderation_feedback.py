"""The author always learns the moderator's decision and can act on it.

Covers: decision notifications (inbox + email intent), the moderator's reason in
the account, "fix and send again" after a rejection, the required reason in the
admin form, and the form fixes (no preselected format, +994 phones, readable
experience errors, success message after sending).
"""
import json
import os
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from catalog.testcases.specialist_document_fixtures import portrait_upload
from catalog.forms import OwnerSpecialistForm
from catalog.models import (EmailOutbox, Region, SiteSettings, Specialist, SpecialistProposalDraft,
                            SpecialistSpecialization, WorkflowNotification)
from catalog.services import specialist_moderation
from catalog.services.specialist_proposal_drafts import save_proposal


class SpecialistModerationFeedbackTests(TestCase):
    def setUp(self):
        from catalog.testcases.workflow_email_helpers import enable_delivery
        enable_delivery(self)
        User = get_user_model()
        self.author = User.objects.create_user('feedback-author', email='feedback-author@example.com')
        self.other = User.objects.create_user('feedback-other')
        self.reviewer = User.objects.create_user('feedback-reviewer', is_staff=True, is_superuser=True)
        self.spec = SpecialistSpecialization.objects.create(code='feedback', name_az='Feedback', name_ru='Feedback', name_en='Feedback')
        self.region = Region.objects.create(key='feedback', name_az='Feedback', name_ru='Feedback', name_en='Feedback')
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def payload(self, **extra):
        data = QueryDict('', mutable=True)
        data.update({'profile_subject': 'other', 'name': 'Feedback applicant', 'bio_ru': 'Biography',
                     'lesson_type': 'individual', 'lesson_price': '25',
                     'consultation_format': 'online', 'phone': '+994501234567', 'language_ru': 'on',
                     'specializations': str(self.spec.pk), 'locations-TOTAL_FORMS': '0',
                     'locations-INITIAL_FORMS': '0', 'locations-MIN_NUM_FORMS': '0', 'locations-MAX_NUM_FORMS': '30'})
        data.update(extra)
        return data

    def submit(self, **extra):
        draft = save_proposal(actor=self.author, draft_id=uuid4(), expected_version='0',
                              data=self.payload(**extra), files={'photo': portrait_upload()}, submit=True)
        return draft, Specialist.objects.get(pk=draft.submitted_specialist_id)

    def admin_action(self, action, person, route='admin:catalog_specialist_changelist', **extra):
        self.client.force_login(self.reviewer)
        data = {'action': action, '_selected_action': str(person.pk), 'index': '0', 'select_across': '0'}
        data.update(extra)
        response = self.client.post(reverse(route), data)
        self.assertEqual(response.status_code, 302)
        person.refresh_from_db()
        return response

    def decisions(self, person):
        return list(WorkflowNotification.objects.filter(
            event_kind='moderation_decision', entity_type='specialist', entity_id=person.pk,
            recipient_user=self.author).order_by('pk').values_list('event_context__decision', flat=True))

    def editor_data(self, person, **changes):
        data = {
            'name': 'Edited profile', 'bio_ru': 'Updated biography', 'status': person.status,
            'specializations': [self.spec.pk], 'language_ru': 'on', 'phone': '+994501234567',
            'session_formats': ['online'], 'lesson_type': 'individual', 'lesson_price': '25',
            'expected_updated_at': person.updated_at.isoformat(),
        }
        for prefix in ('practice_locations', 'documents'):
            data[f'{prefix}-TOTAL_FORMS'] = '0'
            data[f'{prefix}-INITIAL_FORMS'] = '0'
        return {**data, **changes}

    def test_reviewed_profile_can_be_published_with_edits_from_either_editor(self):
        from django.contrib.admin.models import LogEntry
        self.client.force_login(self.reviewer)
        for route in ('catalog_specialist', 'catalog_moderation_moderationspecialist'):
            with self.subTest(route=route):
                _, person = self.submit()
                url = reverse(f'admin:{route}_change', args=[person.pk])
                page = self.client.get(url)
                self.assertContains(page, 'value="publish"')
                data = self.editor_data(person, _specialist_decision='publish', rejection_reason='Old note')
                result = self.client.post(url, data)
                self.assertRedirects(result, reverse(f'admin:{route}_changelist'), fetch_redirect_response=False)
                person.refresh_from_db()
                self.assertEqual((person.status, person.is_active, person.rejection_reason), ('published', True, ''))
                self.assertEqual(person.name, 'Edited profile')
                self.assertEqual(self.decisions(person), ['approved'])
                log = LogEntry.objects.filter(user=self.reviewer, object_id=str(person.pk)).latest('pk')
                self.assertIn('Статус модерации', json.loads(log.change_message)[0]['changed']['fields'])
                self.assertEqual(self.client_class().get(person.get_absolute_url()).status_code, 200)

                ordinary_url = reverse('admin:catalog_specialist_change', args=[person.pk])
                self.assertContains(self.client.get(ordinary_url), 'value="unpublish"')
                self.client.post(ordinary_url, self.editor_data(person, _specialist_decision='unpublish'))
                person.refresh_from_db()
                self.assertEqual((person.status, person.is_active), ('draft', False))
                self.assertEqual(self.client_class().get(person.get_absolute_url()).status_code, 404)

    def test_failed_publish_can_be_corrected_or_saved_without_publishing(self):
        _, person = self.submit()
        self.client.force_login(self.reviewer)
        url = reverse('admin:catalog_specialist_change', args=[person.pk])
        result = self.client.post(url, self.editor_data(person, _specialist_decision='publish',
                                status='draft', lesson_price='', language_ru='', bio_ru='', phone=''))
        self.assertEqual(result.status_code, 200)
        errors = result.context['adminform'].form.errors
        self.assertTrue({'lesson_price', 'language_az', 'phone'}.issubset(errors), errors)
        self.assertTrue(any(key.startswith('bio_') for key in errors), errors)
        stale = self.client.post(url, self.editor_data(person, _specialist_decision='publish', expected_updated_at='old'))
        self.assertTrue(stale.context['adminform'].form.has_error('__all__', 'stale_version'))
        no_office = self.client.post(url, self.editor_data(person, _specialist_decision='publish', session_formats=['office']))
        self.assertEqual(no_office.status_code, 200)
        person.refresh_from_db()
        self.assertFalse(person.offers_office)
        self.assertEqual(person.status, 'pending')
        self.assertEqual(self.client.post(url, self.editor_data(person, _save='1')).status_code, 302)
        person.refresh_from_db()
        self.assertEqual(person.status, 'pending')
        self.assertEqual(self.decisions(person), [])

    def test_new_profile_can_be_saved_and_published_in_one_step(self):
        self.client.force_login(self.reviewer)
        url = reverse('admin:catalog_specialist_add')
        self.assertContains(self.client.get(url), 'value="publish"')
        _, source = self.submit()
        data = self.editor_data(source, _specialist_decision='publish', name='New profile', status='draft')
        data.pop('expected_updated_at')
        self.assertEqual(self.client.post(url, data).status_code, 302)
        created = Specialist.objects.get(name='New profile')
        self.assertEqual((created.status, created.is_active), ('published', True))

    def test_revision_and_rejection_preserve_the_moderators_comment(self):
        self.client.force_login(self.reviewer)
        for action, status, event in [('revise', 'draft', 'needs_changes'), ('reject', 'rejected', 'rejected')]:
            with self.subTest(action=action):
                draft, person = self.submit()
                url = reverse('admin:catalog_moderation_moderationspecialist_change', args=[person.pk])
                self.assertContains(self.client.get(url), f'value="{action}"')
                data = self.editor_data(person, _specialist_decision=action)
                failed = self.client.post(url, data)
                self.assertIn('rejection_reason', failed.context['adminform'].form.errors)
                new_subject = SpecialistSpecialization.objects.create(code=f'new-{action}')
                data.update(rejection_reason='Please clarify.', specializations=[new_subject.pk])
                self.assertEqual(self.client.post(url, data).status_code, 302)
                person.refresh_from_db()
                self.assertEqual((person.status, person.is_active, person.rejection_reason), (status, False, 'Please clarify.'))
                self.assertEqual(self.decisions(person), [event])
                if action == 'revise':
                    draft.refresh_from_db()
                    self.assertIsNone(draft.submitted_at)
                    self.assertEqual(draft.payload['specializations'], [str(new_subject.pk)])

    def test_read_only_staff_cannot_submit_moderation_decisions(self):
        _, person = self.submit()
        viewer = get_user_model().objects.create_user('editor-view-only', is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_specialist'))
        self.client.force_login(viewer)
        for route in ('catalog_specialist', 'catalog_moderation_moderationspecialist'):
            url = reverse(f'admin:{route}_change', args=[person.pk])
            self.assertNotContains(self.client.get(url), 'name="_specialist_decision"')
            self.assertEqual(self.client.post(url, self.editor_data(person, _specialist_decision='publish')).status_code, 403)
        person.refresh_from_db()
        self.assertEqual(person.status, 'pending')

    def test_moderator_can_publish_from_queue_without_private_document_permissions(self):
        _, person = self.submit()
        moderator = get_user_model().objects.create_user('profile-moderator', is_staff=True)
        moderator.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_specialist'))
        self.client.force_login(moderator)
        url = reverse('admin:catalog_moderation_moderationspecialist_change', args=[person.pk])
        page = self.client.get(url)
        self.assertContains(page, 'value="publish"')
        self.assertNotContains(page, 'name="documents-TOTAL_FORMS"')
        self.assertEqual(self.client.post(url, self.editor_data(person, _specialist_decision='publish')).status_code, 302)
        person.refresh_from_db()
        self.assertEqual((person.status, person.is_active), ('published', True))

    def test_reject_with_comment_reaches_author_inbox_email_and_account(self):
        _, person = self.submit()
        self.admin_action('mark_rejected', person, moderation_comment='Нет описания методики.')
        self.assertEqual(person.status, Specialist.STATUS_REJECTED)
        self.assertEqual(person.rejection_reason, 'Нет описания методики.')
        self.assertEqual(self.decisions(person), ['rejected'])
        item = WorkflowNotification.objects.get(entity_type='specialist', entity_id=person.pk)
        self.assertEqual(item.event_context['reason'], 'Нет описания методики.')
        self.assertTrue(EmailOutbox.objects.filter(notification=item, recipient_email='feedback-author@example.com').exists())

        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_index'))
        self.assertContains(page, 'Нет описания методики.')
        self.assertContains(page, reverse('specialist_workspace_reopen', args=[person.pk]))

    def test_reject_without_comment_uses_default_reason(self):
        _, person = self.submit()
        self.admin_action('mark_rejected', person)
        self.assertEqual(person.rejection_reason, specialist_moderation.default_reason(specialist_moderation.REJECTED))

    def test_author_can_fix_and_resend_after_rejection(self):
        _, person = self.submit()
        self.admin_action('mark_rejected', person, moderation_comment='Уточните контакты.')
        self.client.force_login(self.author)
        response = self.client.post(reverse('specialist_workspace_reopen', args=[person.pk]))
        draft = SpecialistProposalDraft.objects.get(submitted_specialist=person)
        self.assertRedirects(response, reverse('specialist_workspace_proposal_resume', args=[draft.pk]),
                             fetch_redirect_response=False)
        person.refresh_from_db()
        self.assertEqual(person.status, Specialist.STATUS_DRAFT)
        self.assertIsNone(draft.submitted_at)
        self.assertEqual(self.client.get(reverse('specialist_workspace_proposal_resume', args=[draft.pk])).status_code, 200)

        resent = save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                               data=self.payload(phone='+994 50 765 43 21'), files={}, submit=True)
        person.refresh_from_db()
        self.assertEqual(resent.submitted_specialist_id, person.pk)
        self.assertEqual(person.status, Specialist.STATUS_PENDING)

    def test_only_the_author_can_reopen(self):
        _, person = self.submit()
        self.admin_action('mark_rejected', person, moderation_comment='Нет.')
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('specialist_workspace_reopen', args=[person.pk])).status_code, 404)
        person.refresh_from_db()
        self.assertEqual(person.status, Specialist.STATUS_REJECTED)

    def test_reopen_refuses_profiles_that_are_not_rejected(self):
        _, person = self.submit()
        self.client.force_login(self.author)
        response = self.client.post(reverse('specialist_workspace_reopen', args=[person.pk]))
        self.assertRedirects(response, reverse('specialist_workspace_index'), fetch_redirect_response=False)
        person.refresh_from_db()
        self.assertEqual(person.status, Specialist.STATUS_PENDING)
        self.assertEqual(self.client.get(reverse('specialist_workspace_reopen', args=[person.pk])).status_code, 405)

    def test_return_for_revision_comment_reopens_draft_and_notifies(self):
        draft, person = self.submit()
        self.admin_action('return_for_revision', person, moderation_comment='Добавьте опыт работы.')
        self.assertEqual(person.status, Specialist.STATUS_DRAFT)
        self.assertEqual(person.rejection_reason, 'Добавьте опыт работы.')
        self.assertEqual(self.decisions(person), ['needs_changes'])
        draft.refresh_from_db()
        self.assertIsNone(draft.submitted_at)
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_index'))
        self.assertContains(page, 'Добавьте опыт работы.')
        self.assertContains(page, reverse('specialist_workspace_proposal_resume', args=[draft.pk]))

    def test_moderation_queue_return_for_revision_uses_the_same_flow(self):
        _, person = self.submit()
        self.admin_action('return_for_revision', person,
                          route='admin:catalog_moderation_moderationspecialist_changelist',
                          moderation_comment='Комментарий из очереди.')
        self.assertEqual(person.rejection_reason, 'Комментарий из очереди.')
        self.assertEqual(self.decisions(person), ['needs_changes'])

    def test_publish_notifies_once_and_links_public_profile(self):
        _, person = self.submit()
        self.admin_action('mark_published', person)
        self.admin_action('mark_published', person)
        self.assertEqual(self.decisions(person), ['approved'])
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_index'))
        self.assertContains(page, person.get_absolute_url())

    def test_change_form_rejection_requires_reason_and_notifies(self):
        _, person = self.submit()
        form_class = __import__('catalog.domain_admin.specialist', fromlist=['SpecialistAdminForm']).SpecialistAdminForm
        form = form_class(instance=person, data={'expected_updated_at': person.updated_at.isoformat()})
        form.cleaned_data = {'status': Specialist.STATUS_REJECTED, 'rejection_reason': ''}
        form._errors = {}
        form.clean()
        self.assertIn('rejection_reason', form.errors)

        previous = person.status
        person.status = Specialist.STATUS_REJECTED
        person.rejection_reason = 'Причина из формы.'
        person.save()
        specialist_moderation.after_admin_status_change(person, previous)
        self.assertEqual(self.decisions(person), ['rejected'])

    def test_send_shows_success_message(self):
        self.client.force_login(self.author)
        data = self.payload(draft_key=str(uuid4()), draft_version='0', form_action='submit')
        data['photo'] = portrait_upload()
        with translation.override('ru'):
            response = self.client.post(reverse('specialist_workspace_proposal'), data, follow=True)
            expected = translation.gettext('Анкета отправлена на проверку.')
        self.assertContains(response, expected)


    def test_outbox_runner_sends_decision_email_without_private_comment(self):
        from django.core import mail
        from django.core.management import call_command
        from django.test import override_settings
        _, person = self.submit()
        self.admin_action('mark_rejected', person, moderation_comment='Секретная деталь модерации.')
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                               PUBLIC_BASE_URL='https://kidsmap.az'):
            call_command('deliver_workflow_outbox', '--send', stdout=open(os.devnull, 'w'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['feedback-author@example.com'])
        self.assertIn('Anketiniz rədd edildi', message.subject)
        self.assertIn('Анкета отклонена', message.subject)
        self.assertIn('Feedback applicant', message.body)
        self.assertIn('https://kidsmap.az', message.body)
        self.assertNotIn('Секретная деталь', message.body)
        row = EmailOutbox.objects.get(notification__entity_type='specialist', notification__entity_id=person.pk)
        self.assertEqual(row.status, 'sent')

    def test_smtp_failure_is_retried_not_lost(self):
        from smtplib import SMTPException
        from unittest.mock import patch
        from catalog.services.workflow_notifications import deliver_batch
        _, person = self.submit()
        self.admin_action('mark_published', person)
        with patch('catalog.services.workflow_notifications.send_mail', side_effect=SMTPException('down')):
            self.assertEqual(deliver_batch(limit=5)['retry'], 1)
        row = EmailOutbox.objects.get(notification__entity_type='specialist', notification__entity_id=person.pk)
        self.assertEqual(row.status, 'retry')
        self.assertIsNotNone(row.next_attempt_at)


class SpecialistFormFixesTests(TestCase):
    def test_new_profile_has_no_preselected_format(self):
        form = OwnerSpecialistForm()
        self.assertEqual(form.initial.get('consultation_format'), '')
        self.assertIn('', [value for value, _ in form.fields['consultation_format'].choices])

    def test_phone_is_stored_in_international_form(self):
        spec = SpecialistSpecialization.objects.create(code='form-fix', name_az='F', name_ru='F', name_en='F')
        form = OwnerSpecialistForm(data={'name': 'Form fix', 'consultation_format': 'online', 'bio_ru': 'Bio',
                                         'lesson_type': 'individual', 'lesson_price': '25',
                                         'phone': '050 123 45 67', 'whatsapp': '+994 55 765 43 21',
                                         'language_ru': 'on', 'specializations': [str(spec.pk)]})
        form.is_valid()
        self.assertEqual(form.cleaned_data.get('phone'), '+994501234567')
        self.assertEqual(form.cleaned_data.get('whatsapp'), '+994557654321')

    def test_experience_error_is_readable(self):
        with translation.override('en'):
            form = OwnerSpecialistForm(data={'experience_years': '-2'}, draft_save_only=True)
            self.assertFalse(form.is_valid())
            self.assertIn('whole years', str(form.errors['experience_years']))
        with translation.override('az'):
            form = OwnerSpecialistForm(data={'experience_years': 'abc'}, draft_save_only=True)
            self.assertFalse(form.is_valid())
            self.assertIn('tam illərlə', str(form.errors['experience_years']))
