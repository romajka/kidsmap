"""Moderation permissions and an author's returned application lifecycle."""
from uuid import uuid4

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.models import (Region, SiteSettings, Specialist, SpecialistClaim,
                            SpecialistDocument, SpecialistProposalDraft, SpecialistSpecialization)
from catalog.proxy_apps.catalog_moderation.models import ModerationSpecialist
from catalog.services.specialist_proposal_drafts import proposal_data, save_proposal


class SpecialistModerationRecoveryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user('revision-author')
        self.other = User.objects.create_user('revision-other')
        self.viewer = User.objects.create_user('revision-viewer', is_staff=True)
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_specialist'))
        self.reviewer = User.objects.create_user('revision-reviewer', is_staff=True, is_superuser=True)
        self.spec = SpecialistSpecialization.objects.create(code='revision', name_az='Revision', name_ru='Revision', name_en='Revision')
        self.region = Region.objects.create(key='revision', name_az='Revision', name_ru='Revision', name_en='Revision')
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def payload(self, **extra):
        data = QueryDict('', mutable=True)
        data.update({'profile_subject':'self', 'name':'Revision applicant', 'bio_ru':'Original biography',
                     'consultation_format':'offline', 'phone':'+994501234567', 'language_ru':'on',
                     'specializations':str(self.spec.pk), 'locations-TOTAL_FORMS':'1',
                     'locations-INITIAL_FORMS':'0', 'locations-MIN_NUM_FORMS':'0', 'locations-MAX_NUM_FORMS':'30',
                     'locations-0-address':'Synthetic office', 'locations-0-region':str(self.region.pk),
                     'locations-0-is_active':'on', 'locations-0-is_primary':'on'})
        data.update(extra)
        return data

    def submit(self, **extra):
        return save_proposal(actor=self.author, draft_id=uuid4(), expected_version='0',
                             data=self.payload(**extra), files={}, submit=True)

    def action(self, route, action, person, actor=None):
        self.client.force_login(actor or self.reviewer)
        return self.client.post(reverse(route), {'action':action, '_selected_action':str(person.pk),
                                                  'index':'0', 'select_across':'0'})

    def return_application(self, draft):
        response = self.action('admin:catalog_moderation_moderationspecialist_changelist',
                               'return_for_revision', draft.submitted_specialist)
        self.assertEqual(response.status_code, 302)
        draft.refresh_from_db()
        return draft

    def test_view_only_staff_cannot_mutate_either_queue(self):
        for route, actions in (
            ('admin:catalog_specialist_changelist', ('mark_published','mark_draft','mark_pending','mark_rejected')),
            ('admin:catalog_moderation_moderationspecialist_changelist', ('mark_published','mark_rejected','return_for_revision')),
        ):
            for action in actions:
                with self.subTest(route=route, action=action):
                    person = self.submit().submitted_specialist
                    before = (person.status, person.is_active, person.updated_at)
                    response = self.action(route, action, person, self.viewer)
                    self.assertEqual(response.status_code, 403)
                    person.refresh_from_db()
                    self.assertEqual((person.status, person.is_active, person.updated_at), before)

    def test_direct_handlers_recheck_change_permission(self):
        person = self.submit().submitted_specialist
        request = RequestFactory().post('/admin/')
        request.user = self.viewer
        request.session = {}
        request._messages = FallbackStorage(request)
        for model, actions in ((Specialist, ('mark_published','mark_draft','mark_pending','mark_rejected')),
                               (ModerationSpecialist, ('return_for_revision',))):
            for action in actions:
                with self.subTest(model=model.__name__, action=action):
                    with self.assertRaises(PermissionDenied):
                        getattr(admin.site._registry[model], action)(request, model.objects.filter(pk=person.pk))
        person.refresh_from_db()
        self.assertEqual(person.status, 'pending')

    def test_return_reopens_application_and_resubmits_same_profile_without_claim_duplicate(self):
        draft = self.submit()
        person = draft.submitted_specialist
        person.photo = 'specialists/photos/existing-synthetic.jpg'
        person.save(update_fields=['photo'])
        document = SpecialistDocument.objects.create(specialist=person, name='Existing evidence',
                                                     document_type='certificate', file='synthetic.pdf')
        original_location = person.practice_locations.get()
        claim = SpecialistClaim.objects.get(specialist=person)
        old_version = draft.version
        self.return_application(draft)
        self.assertIsNone(draft.submitted_at)
        self.assertGreater(draft.version, old_version)
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_proposal_resume', args=[draft.pk]))
        self.assertEqual(page.status_code, 200)
        data = proposal_data(draft.payload)
        data['bio_ru'] = 'Corrected biography'
        saved = save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                              data=data, files={}, submit=True)
        self.assertEqual(saved.submitted_specialist_id, person.pk)
        person.refresh_from_db()
        self.assertEqual(person.bio_ru, 'Corrected biography')
        self.assertEqual(person.status, 'pending')
        self.assertEqual(person.photo.name, 'specialists/photos/existing-synthetic.jpg')
        self.assertTrue(person.documents.filter(pk=document.pk).exists())
        self.assertEqual(list(person.practice_locations.values_list('pk', flat=True)), [original_location.pk])
        self.assertEqual(list(person.person_claims.values_list('pk', flat=True)), [claim.pk])
        repeated = save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                                 data=data, files={}, submit=True)
        self.assertEqual(repeated.submitted_specialist_id, person.pk)
        self.assertEqual(Specialist.objects.count(), 1)
        self.return_application(saved)
        self.assertIsNone(saved.submitted_at)

    def test_returned_draft_cannot_be_used_by_another_actor(self):
        draft = self.return_application(self.submit())
        with self.assertRaises(PermissionDenied):
            save_proposal(actor=self.other, draft_id=draft.pk, expected_version=str(draft.version),
                          data=proposal_data(draft.payload), files={}, submit=True)

    def test_returned_draft_cannot_overwrite_profile_published_after_return(self):
        draft = self.return_application(self.submit())
        Specialist.objects.filter(pk=draft.submitted_specialist_id).update(status='published')
        with self.assertRaises(ValidationError):
            save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                          data=proposal_data(draft.payload), files={}, submit=True)

    def test_publish_does_not_approve_identity_and_admin_shows_separate_review(self):
        draft = self.submit()
        person = draft.submitted_specialist
        self.action('admin:catalog_specialist_changelist','mark_published',person)
        person.refresh_from_db()
        self.assertIsNone(person.verified_person_user_id)
        self.assertEqual(SpecialistClaim.objects.get(specialist=person).status,'pending')
        page = self.client.get(reverse('admin:catalog_specialist_change', args=[person.pk]))
        self.assertTrue('specialist_pending_claim_count' in page.context)
        self.assertEqual(page.context['specialist_pending_claim_count'], 1)
        self.assertTrue(page.context['specialist_public_visible'])
        self.assertEqual(page.context['specialist_identity_review_url'],
                         reverse('specialist_workspace_review', args=[person.pk]))
        self.assertEqual(page.context['specialist_pending_claims'][0].applicant_id, self.author.pk)

    def test_identity_review_link_remains_discoverable_after_publication_for_reviewer_only(self):
        person = self.submit().submitted_specialist
        self.action('admin:catalog_specialist_changelist', 'mark_published', person)
        review_url = reverse('specialist_workspace_review', args=[person.pk])
        page = self.client.get(reverse('admin:catalog_specialist_changelist'))
        self.assertTrue(review_url.encode() in page.content)
        self.client.force_login(self.viewer)
        page = self.client.get(reverse('admin:catalog_specialist_changelist'))
        self.assertNotContains(page, review_url)

    def test_return_preserves_other_proposal_without_creating_person_claim(self):
        draft = self.return_application(self.submit(profile_subject='other'))
        sent = save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                             data=proposal_data(draft.payload), files={}, submit=True)
        self.assertEqual(sent.submitted_specialist_id, draft.submitted_specialist_id)
        self.assertFalse(SpecialistClaim.objects.exists())

    def test_returned_draft_cannot_target_another_authors_profile(self):
        draft = self.return_application(self.submit())
        other_profile = Specialist.objects.create(name='Other private person', created_by=self.other)
        SpecialistProposalDraft.objects.filter(pk=draft.pk).update(submitted_specialist=other_profile)
        with self.assertRaises(PermissionDenied):
            save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                          data=proposal_data(draft.payload), files={}, submit=True)

    def test_returned_application_photo_clear_survives_draft_reload_and_submit(self):
        draft = self.submit()
        person = draft.submitted_specialist
        person.photo = 'specialists/photos/previous-synthetic.jpg'
        person.save(update_fields=['photo'])
        self.return_application(draft)
        data = proposal_data(draft.payload)
        data['photo-clear'] = 'on'
        saved = save_proposal(actor=self.author, draft_id=draft.pk, expected_version=str(draft.version),
                              data=data, files={}, submit=False)
        person.refresh_from_db()
        self.assertTrue(person.photo)  # A working-copy save does not mutate the submitted profile.
        self.assertEqual(saved.payload.get('photo-clear'), ['on'])
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_proposal_resume', args=[draft.pk]))
        self.assertFalse(page.context['form']['photo'].value())
        data = proposal_data(saved.payload)
        data.pop('photo-clear')  # Cleared preview no longer contains the original file checkbox.
        sent = save_proposal(actor=self.author, draft_id=saved.pk, expected_version=str(saved.version),
                             data=data, files={}, submit=True)
        self.assertFalse(sent.submitted_specialist.photo)
