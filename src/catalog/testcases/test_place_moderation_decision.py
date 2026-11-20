"""Moderator sends a place back or declines it, always with a reason the author
sees in the moderation queue result, the cabinet, the inbox and the email."""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, VolunteerPlaceRevision, WorkflowNotification
from catalog.services import publication
from catalog.services.workflow_notifications import deliver_batch
from catalog.testcases.utils import create_quality_place

QUEUE = 'admin:catalog_moderation_moderationplace_changelist'


class PlaceModerationDecisionTests(TestCase):
    def setUp(self):
        from catalog.testcases.workflow_email_helpers import enable_delivery
        enable_delivery(self)
        users = get_user_model()
        self.owner = users.objects.create_user('decision_owner', email='owner@example.invalid')
        self.staff = users.objects.create_superuser('decision_staff', 'staff@example.invalid', 'synthetic')
        self.client.force_login(self.staff)

    def candidate_place(self):
        """A published card with a pending owner edit (versioned candidate)."""
        place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True,
                                     name_az='Rəngli Studiya', name_ru='Цветная студия', name_en='Color Studio')
        publication.propose(actor=self.owner, target_type='place', target_id=place.pk,
                            patch={'description_az': 'Uşaqlar üçün yaşa uyğun rəsm dərsləri və emalatxanalar.'},
                            schema_version=1, expected_version=place.content_version,
                            revision_version=0, submit=True)
        return place

    def legacy_place(self):
        """A pending card without a candidate version."""
        return create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True,
                                    status=Place.STATUS_PENDING, is_active=False,
                                    name_az='Kiçik Gimnastlar', name_ru='Маленькие гимнасты', name_en='Little Gymnasts')

    def act(self, action, place, comment):
        return self.client.post(reverse(QUEUE), {
            'action': action, '_selected_action': [place.pk], 'select_across': '0', 'index': '0',
            'moderation_comment': comment}, follow=True)

    def test_queue_renders_decision_buttons_and_dialog(self):
        place = self.candidate_place()
        response = self.client.get(reverse(QUEUE))
        self.assertContains(response, f'data-km-decide="return_for_revision" data-place-id="{place.pk}"', count=1)
        self.assertContains(response, f'data-km-decide="mark_rejected" data-place-id="{place.pk}"', count=1)
        self.assertContains(response, 'id="km-decision-template"')
        self.assertContains(response, 'kidsmap_moderation_decision.js')

    def test_without_a_reason_nothing_changes(self):
        place = self.candidate_place()
        response = self.act('return_for_revision', place, '   ')
        self.assertContains(response, 'Укажите причину')
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=place).status, 'pending')
        self.assertFalse(WorkflowNotification.objects.exists())

    def test_candidate_sent_back_with_reason_everywhere(self):
        place = self.candidate_place()
        reason = 'Добавьте фото помещения.\nУточните расписание.'
        response = self.act('return_for_revision', place, reason)
        self.assertContains(response, 'На доработку отправлено: 1')
        revision = VolunteerPlaceRevision.objects.get(place=place)
        self.assertEqual((revision.status, revision.review_note), ('rejected', reason))
        item = WorkflowNotification.objects.get(entity_type='volunteer_revision', entity_id=revision.pk)
        self.assertEqual(item.event_context['decision'], 'needs_changes')
        self.assertNotIn(place.pk, list(self.client.get(reverse(QUEUE)).context['cl'].result_list.values_list('pk', flat=True)))

        self.assertEqual(deliver_batch()['sent'], 1)
        message = mail.outbox[0]
        self.assertIn('Нужна доработка', message.subject)
        self.assertIn('Rəngli Studiya', message.subject)
        self.assertIn('Уточните расписание.', message.body)
        self.assertIn('Текущая версия на сайте не меняется', message.body)
        html = message.alternatives[0][0]
        self.assertIn('Добавьте фото помещения.<br>Уточните расписание.', html)

        self.client.force_login(self.owner)
        cabinet = self.client.get('/ru/account/places/')
        self.assertContains(cabinet, 'Модератор просит доработать')
        self.assertContains(cabinet, 'Уточните расписание.')
        self.assertContains(cabinet, 'Исправьте отмеченное и отправьте на проверку снова.')

    def test_candidate_declined_is_final(self):
        place = self.candidate_place()
        self.act('mark_rejected', place, 'Дубликат существующей карточки.')
        revision = VolunteerPlaceRevision.objects.get(place=place)
        self.assertEqual(revision.status, 'declined')
        self.assertEqual(deliver_batch()['sent'], 1)
        self.assertIn('Отклонено', mail.outbox[0].subject)
        self.assertIn('Дубликат существующей карточки.', mail.outbox[0].body)

    def test_legacy_card_declined_with_reason_inbox_and_email(self):
        place = self.legacy_place()
        response = self.act('mark_rejected', place, 'Место не относится к детским занятиям.')
        self.assertContains(response, 'Отклонено: 1')
        place.refresh_from_db()
        self.assertEqual((place.status, place.is_active), (Place.STATUS_REJECTED, False))
        self.assertEqual(place.rejection_reason, 'Место не относится к детским занятиям.')
        item = WorkflowNotification.objects.get(entity_type='place', entity_id=place.pk)
        self.assertEqual((item.event_context['decision'], item.recipient_user), ('rejected', self.owner))

        self.assertEqual(deliver_batch()['sent'], 1)
        message = mail.outbox[0]
        self.assertIn('Отклонено', message.subject)
        self.assertIn('не будет опубликовано', message.body)
        self.assertIn('Место не относится к детским занятиям.', message.alternatives[0][0])

        self.client.force_login(self.owner)
        inbox = self.client.get('/ru/account/notifications/')
        self.assertContains(inbox, 'Отклонено')
        self.assertContains(inbox, 'Маленькие гимнасты')
        self.assertContains(inbox, 'Место не относится к детским занятиям.')

    def test_legacy_card_sent_back_can_be_fixed(self):
        place = self.legacy_place()
        self.act('return_for_revision', place, 'Укажите рабочий телефон.')
        place.refresh_from_db()
        self.assertEqual(place.status, Place.STATUS_NEEDS_CHANGES)
        self.client.force_login(self.owner)
        cabinet = self.client.get('/ru/account/places/')
        self.assertContains(cabinet, 'Укажите рабочий телефон.')
        self.assertContains(cabinet, reverse('owner_place_edit', args=[place.pk]))

    def test_second_decision_after_resubmission_is_a_new_email(self):
        place = self.legacy_place()
        self.act('return_for_revision', place, 'Первая причина.')
        Place.objects.filter(pk=place.pk).update(status=Place.STATUS_PENDING)
        self.act('mark_rejected', place, 'Вторая причина.')
        self.assertEqual(WorkflowNotification.objects.filter(entity_type='place', entity_id=place.pk).count(), 2)

    def test_reason_html_is_escaped_in_email(self):
        place = self.legacy_place()
        self.act('return_for_revision', place, '<b>bold</b> <script>x()</script>')
        deliver_batch()
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>x()', html)
