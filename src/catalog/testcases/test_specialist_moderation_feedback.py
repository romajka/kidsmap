"""The author always learns the moderator's decision and can act on it.

Covers: decision notifications (inbox + email intent), the moderator's reason in
the account, "fix and send again" after a rejection, the required reason in the
admin form, and the form fixes (no preselected format, +994 phones, readable
experience errors, success message after sending).
"""
import os
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

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
                     'consultation_format': 'online', 'phone': '+994501234567', 'language_ru': 'on',
                     'specializations': str(self.spec.pk), 'locations-TOTAL_FORMS': '0',
                     'locations-INITIAL_FORMS': '0', 'locations-MIN_NUM_FORMS': '0', 'locations-MAX_NUM_FORMS': '30'})
        data.update(extra)
        return data

    def submit(self, **extra):
        draft = save_proposal(actor=self.author, draft_id=uuid4(), expected_version='0',
                              data=self.payload(**extra), files={}, submit=True)
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
        with translation.override('ru'):
            response = self.client.post(reverse('specialist_workspace_proposal'), data, follow=True)
            expected = translation.gettext('Анкета отправлена на проверку. О решении модератора мы сообщим в уведомлениях и по email.')
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
