"""Moderation decisions retain their meaning without granting stale access."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import EmailOutbox, Place, WorkflowNotification
from catalog.services import publication
from catalog.services.workflow_notifications import emit
from catalog.testcases.utils import create_quality_place


class OwnerLifecycleNotificationTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('notice_owner', email='owner@example.invalid')
        self.other = users.objects.create_user('notice_other', email='other@example.invalid')
        self.staff = users.objects.create_superuser('notice_staff', 'staff@example.invalid', 'synthetic')
        self.place = create_quality_place(
            owner=self.owner, created_by=self.owner, with_subcategory=True, name_az='Kiçik Kəşflər',
            name_ru='Маленькие открытия', name_en='Little Discoveries')

    def propose(self, description):
        from catalog.models import VolunteerPlaceRevision
        self.place.refresh_from_db()
        current = VolunteerPlaceRevision.objects.filter(place=self.place).first()
        return publication.propose(
            actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'description_az': description}, schema_version=1,
            expected_version=self.place.content_version,
            revision_version=current.version if current else 0, submit=True)

    def decide(self, *, approve=False, note='Уточните возраст группы', final_reject=False):
        revision = self.propose('Uşaqlar üçün yaşa uyğun yaradıcılıq dərsləri.')
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
                           approve=approve, note=note, final_reject=final_reject)
        return WorkflowNotification.objects.get(entity_id=revision.pk, entity_version=revision.version + 1)

    def test_rejection_and_approval_remain_distinct_after_a_later_edit(self):
        rejected = self.decide()
        approved = self.decide(approve=True, note='')
        Place.objects.filter(pk=self.place.pk).update(name_ru='Позднее название')
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/notifications/')
        self.assertContains(response, 'Нужны исправления')
        self.assertContains(response, 'Одобрено')
        self.assertContains(response, 'Маленькие открытия', count=2)
        self.assertNotContains(response, 'Позднее название')
        self.assertContains(response, 'Уточните возраст группы')
        self.assertContains(response, reverse('owner_place_edit', args=[self.place.pk]), count=2)
        rejected.refresh_from_db(); approved.refresh_from_db()
        self.assertEqual(rejected.event_context['decision'], 'needs_changes')
        self.assertEqual(approved.event_context['decision'], 'approved')

    def test_decisions_and_entity_titles_are_localized(self):
        self.decide()
        self.client.force_login(self.owner)
        for path, title, decision in [
            ('/account/notifications/', 'Kiçik Kəşflər', 'Düzəliş lazımdır'),
            ('/ru/account/notifications/', 'Маленькие открытия', 'Нужны исправления'),
            ('/en/account/notifications/', 'Little Discoveries', 'Changes requested'),
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, decision)
                self.assertContains(response, title)

    def test_final_rejection_does_not_look_like_a_request_for_changes(self):
        item = self.decide(final_reject=True)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get('/ru/account/notifications/'), 'Отклонено')
        self.assertEqual(item.event_context['decision'], 'rejected')

    def test_reemit_preserves_original_decision_and_one_email_intent(self):
        item = self.decide()
        self.assertEqual(getattr(item, 'event_context', {}).get('decision'), 'needs_changes')
        before = item.event_context.copy()
        again = emit(kind=item.event_kind, entity_type=item.entity_type, entity_id=item.entity_id,
                     version=item.entity_version, recipient_user=self.owner)
        self.assertEqual(again.pk, item.pk)
        self.assertEqual(again.event_context, before)
        self.assertEqual(EmailOutbox.objects.filter(notification=item).count(), 1)

    def test_revoked_owner_gets_no_private_title_reason_or_editor_link(self):
        self.decide()
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/notifications/')
        self.assertContains(response, 'Решение модерации')
        self.assertNotContains(response, 'Маленькие открытия')
        self.assertNotContains(response, 'Уточните возраст группы')
        self.assertNotContains(response, reverse('owner_place_edit', args=[self.place.pk]))

    def test_other_account_cannot_read_private_decision(self):
        item = self.decide()
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get('/ru/account/notifications/'), 'Уточните возраст группы')
        self.assertEqual(self.client.post(reverse('account_notification_read', args=[item.pk])).status_code, 404)

    def test_reason_is_escaped_and_not_copied_into_email(self):
        from django.core import mail
        from catalog.services.workflow_notifications import deliver_batch
        self.decide(note='<script>alert("private-note")</script>')
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/notifications/')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert("private-note")</script>')
        self.assertEqual(deliver_batch()['sent'], 1)
        self.assertNotIn('private-note', mail.outbox[0].body)

    def test_legacy_event_does_not_guess_current_decision(self):
        emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=999,
             version=1, recipient_user=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/notifications/')
        self.assertContains(response, 'Решение модерации')
        self.assertNotContains(response, 'Маленькие открытия')
        self.assertNotContains(response, 'Одобрено')

    def test_malformed_stored_context_falls_back_without_a_server_error(self):
        item = self.decide()
        context = item.event_context.copy()
        context['decision'] = ['not-a-decision']
        WorkflowNotification.objects.filter(pk=item.pk).update(event_context=context)
        self.client.force_login(self.owner)
        self.client.raise_request_exception = False
        response = self.client.get('/ru/account/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Решение модерации')
        self.assertNotContains(response, 'Маленькие открытия')

    def test_forged_target_does_not_produce_a_link_or_private_snapshot(self):
        item = self.decide()
        context = item.event_context.copy()
        context['target_id'] = self.place.pk + 1000
        context['url'] = 'https://untrusted.invalid/'
        WorkflowNotification.objects.filter(pk=item.pk).update(event_context=context)
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/notifications/')
        self.assertContains(response, 'Решение модерации')
        self.assertNotContains(response, 'Маленькие открытия')
        self.assertNotContains(response, 'https://untrusted.invalid/')

    def test_missing_title_translation_falls_back_to_the_original_az_title(self):
        Place.objects.filter(pk=self.place.pk).update(name_ru='', name_en='')
        self.decide()
        self.client.force_login(self.owner)
        self.assertContains(self.client.get('/en/account/notifications/'), 'Kiçik Kəşflər')

    def test_other_publication_targets_link_to_the_current_authorized_workspace(self):
        from catalog.models import Activity, OfferingGroup, Organization, Program
        org = Organization.objects.create(owner=self.owner, name_az='Şəbəkə')
        program = Program.objects.create(organization=org, name_az='Proqram')
        activity = Activity.objects.create(place=self.place, name_az='Məşğələ')
        group = OfferingGroup.objects.create(activity=activity, name_az='Qrup')
        self.client.force_login(self.owner)
        for kind, target, route, args in [
            ('organization', org, 'organization_workspace_detail', [org.pk]),
            ('program', program, 'organization_program_detail', [org.pk, program.pk]),
            ('activity', activity, 'owner_place_edit', [self.place.pk]),
            ('offering_group', group, 'owner_place_edit', [self.place.pk]),
        ]:
            with self.subTest(kind=kind):
                revision = publication.propose(actor=self.owner, target_type=kind, target_id=target.pk,
                    patch={'name_az': target.name_az + ' yeni'}, schema_version=1,
                    expected_version=target.content_version)
                publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
                                   approve=False, note='Ətraflı məlumat əlavə edin')
                with override('az'):
                    expected_url = reverse(route, args=args)
                response = self.client.get('/account/notifications/')
                self.assertContains(response, 'Düzəliş lazımdır')
                self.assertContains(response, target.name_az + ' yeni')
                self.assertContains(response, 'href="' + expected_url + '"')
