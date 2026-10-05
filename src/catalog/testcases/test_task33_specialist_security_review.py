"""Independent stage24 security negatives; only synthetic actors and file bytes."""
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.admin import AdminSite
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import TestCase, RequestFactory, override_settings
from django.utils import timezone
from django.urls import reverse
from catalog.models import Specialist, SpecialistDocument, SiteSettings
from catalog.services.specialist_documents import review_document, set_document_public_choice
from catalog.views import serve_specialist_document
from catalog.domain_admin.specialist import SpecialistDocumentInline


class IndependentSpecialistSecurityTests(TestCase):
    def setUp(self):
        self.public = TemporaryDirectory()
        self.private = TemporaryDirectory()
        self.addCleanup(self.public.cleanup)
        self.addCleanup(self.private.cleanup)
        self.settings = override_settings(MEDIA_ROOT=self.public.name, PRIVATE_MEDIA_ROOT=self.private.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.person_actor = get_user_model().objects.create_user('independent-person')
        self.manager = get_user_model().objects.create_user('independent-manager')
        self.reviewer = get_user_model().objects.create_user('independent-reviewer', is_staff=True)
        self.permission = Permission.objects.get(codename='review_specialist_documents')
        self.reviewer.user_permissions.add(self.permission)
        self.person = Specialist.objects.create(name='Independent synthetic person', slug='independent-person',
            owner=self.manager, verified_person_user=self.person_actor, person_verified_at=timezone.now(),
            status='published', is_active=True)
        self.document = SpecialistDocument.objects.create(specialist=self.person, name='Private synthetic certificate',
            document_type='certificate', file=SimpleUploadedFile('certificate.pdf', b'%PDF-synthetic-only'),
            status='pending')

    def request(self, actor):
        request = RequestFactory().get('/synthetic-document')
        request.user = actor
        return request

    def test_management_owner_cannot_read_or_choose_person_document_publication(self):
        with self.assertRaises(Http404):
            serve_specialist_document(self.request(self.manager), self.document.pk)
        with self.assertRaises(PermissionError):
            set_document_public_choice(actor=self.manager, document_id=self.document.pk, publish=True)
        self.document.refresh_from_db()
        self.assertFalse(self.document.is_published)
        self.assertIsNone(self.document.opted_in_by_id)

    def test_revoked_cached_permission_cannot_approve_after_reviewer_lock(self):
        self.assertTrue(self.reviewer.has_perm('catalog.review_specialist_documents'))
        self.reviewer.user_permissions.clear()
        with self.assertRaises(PermissionError):
            review_document(actor=self.reviewer, document_id=self.document.pk, approve=True)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'pending')

    def test_deactivated_cached_person_cannot_create_public_consent(self):
        get_user_model().objects.filter(pk=self.person_actor.pk).update(is_active=False)
        with self.assertRaises(PermissionError):
            set_document_public_choice(actor=self.person_actor, document_id=self.document.pk, publish=True)
        self.document.refresh_from_db()
        self.assertFalse(self.document.is_published)

    def test_pending_consent_and_identity_tamper_remain_private_to_anonymous(self):
        for kind, status in [('certificate', 'pending'), ('identity', 'approved')]:
            with self.subTest(kind=kind, status=status):
                document = SpecialistDocument.objects.create(specialist=self.person, document_type=kind,
                    name='Synthetic pending or identity evidence',
                    file=SimpleUploadedFile('evidence.pdf', b'%PDF-private-only'), status=status,
                    is_published=True, opted_in_by=self.person_actor, opted_in_at=timezone.now())
                with self.assertRaises(Http404):
                    serve_specialist_document(self.request(AnonymousUser()), document.pk)

    def test_ineligible_public_profile_and_inactive_person_cannot_publish_document(self):
        self.document.status = 'approved'
        self.document.is_published = True
        self.document.opted_in_by = self.person_actor
        self.document.opted_in_at = timezone.now()
        self.document.save()
        for status, active in [('draft', True), ('published', False)]:
            with self.subTest(status=status, active=active):
                Specialist.objects.filter(pk=self.person.pk).update(status=status, is_active=active)
                with self.assertRaises(Http404):
                    serve_specialist_document(self.request(AnonymousUser()), self.document.pk)
        Specialist.objects.filter(pk=self.person.pk).update(status='published', is_active=True)
        get_user_model().objects.filter(pk=self.person_actor.pk).update(is_active=False)
        with self.assertRaises(Http404):
            serve_specialist_document(self.request(AnonymousUser()), self.document.pk)
        response = self.client.get('/specialists/independent-person/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private synthetic certificate')

    def test_inline_uses_dedicated_permission_without_file_or_consent_write_fields(self):
        inline = SpecialistDocumentInline(Specialist, AdminSite())
        for actor, allowed in [(self.manager, False), (self.reviewer, True)]:
            with self.subTest(actor=actor.username):
                request = self.request(actor)
                self.assertEqual(inline.has_view_permission(request, self.person), allowed)
                self.assertEqual(inline.has_change_permission(request, self.person), allowed)
                self.assertFalse(inline.has_add_permission(request, self.person))
                self.assertFalse(inline.has_delete_permission(request, self.person))
        formset = inline.get_formset(self.request(self.reviewer), self.person)
        for field in ('file', 'is_published', 'opted_in_at', 'opted_in_by', 'document_type'):
            self.assertNotIn(field, formset.form.base_fields)

    def test_person_choice_approval_and_withdrawal_preserve_private_evidence(self):
        set_document_public_choice(actor=self.person_actor, document_id=self.document.pk, publish=True)
        with self.assertRaises(Http404):
            serve_specialist_document(self.request(AnonymousUser()), self.document.pk)
        review_document(actor=self.reviewer, document_id=self.document.pk, approve=True)
        response = serve_specialist_document(self.request(AnonymousUser()), self.document.pk)
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'%PDF-synthetic-only')
            self.assertIn('attachment', response['Content-Disposition'])
            self.assertEqual(response['Cache-Control'], 'private, no-store')
        finally:
            # FileResponse.close emits request_finished and closes TestCase's DB.
            for closer in response._resource_closers:
                closer()
        set_document_public_choice(actor=self.person_actor, document_id=self.document.pk, publish=False)
        with self.assertRaises(Http404):
            serve_specialist_document(self.request(AnonymousUser()), self.document.pk)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'approved')
        self.assertIsNone(self.document.opted_in_by_id)
        self.assertTrue(self.document.file.storage.exists(self.document.file.name))

    def test_ordinary_admin_cannot_observe_private_document_count(self):
        from catalog.domain_admin.specialist import SpecialistAdmin
        model_admin = SpecialistAdmin(Specialist, AdminSite())
        self.manager.is_staff = True
        self.manager.save(update_fields=['is_staff'])
        self.manager.user_permissions.add(Permission.objects.get(codename='view_specialist'))
        self.assertNotIn('documents_count', model_admin.get_list_display(self.request(self.manager)))
        self.assertIn('documents_count', model_admin.get_list_display(self.request(self.reviewer)))

    def test_non_boolean_public_choice_is_rejected_without_consent(self):
        with self.assertRaises(ValidationError):
            set_document_public_choice(actor=self.person_actor, document_id=self.document.pk, publish='false')
        self.document.refresh_from_db()
        self.assertFalse(self.document.is_published)
        self.assertIsNone(self.document.opted_in_by_id)

    def test_non_boolean_review_decision_is_rejected_without_approval(self):
        with self.assertRaises(ValidationError):
            review_document(actor=self.reviewer, document_id=self.document.pk, approve='reject')
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'pending')

    def test_saved_identity_purpose_cannot_be_relabeled_public_certificate(self):
        identity = SpecialistDocument.objects.create(specialist=self.person, document_type='identity',
            name='Synthetic immutable identity', file=SimpleUploadedFile('identity.pdf', b'%PDF-private-only'))
        identity.document_type = 'certificate'
        identity.status = 'approved'
        identity.is_published = True
        identity.opted_in_by = self.person_actor
        identity.opted_in_at = timezone.now()
        with self.assertRaises(ValidationError):
            identity.save()
        identity.refresh_from_db()
        self.assertEqual(identity.document_type, 'identity')
        self.assertFalse(identity.is_published)

    def test_personal_editor_denies_legacy_manager_and_accepts_verified_person(self):
        url = reverse('owner_specialist_edit', args=[self.person.pk])
        for actor, expected in [(self.manager, 404), (self.person_actor, 200)]:
            with self.subTest(actor=actor.username):
                self.client.force_login(actor)
                self.assertEqual(self.client.get(url).status_code, expected)

    def test_personal_cabinet_lists_verified_person_not_legacy_manager(self):
        url = reverse('owner_places_dashboard')
        self.client.force_login(self.manager)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Independent synthetic person')
        self.client.force_login(self.person_actor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Independent synthetic person')

    def test_live_place_owner_and_organization_grantee_cannot_read_person_documents(self):
        from catalog.models import Organization, OrganizationGrant
        from catalog.services.organization_ownership import request_join
        from catalog.services.place_access import has_place_permission
        from catalog.testcases.utils import create_quality_place
        member = get_user_model().objects.create_user('independent-business-member')
        place = create_quality_place(owner=self.manager, created_by=self.manager)
        organization = Organization.objects.create(owner=self.manager, created_by=self.manager,
            name_az='Independent synthetic business', status='published', approved_at=timezone.now())
        request_join(actor=self.manager, place_id=place.pk, organization_id=organization.pk)
        place.refresh_from_db()
        OrganizationGrant.objects.create(organization=organization, owner=self.manager, member=member,
            base_ownership_version=organization.ownership_version, scope='all_network',
            actions=['organization.view', 'place.view', 'place.edit'])
        for actor in (self.manager, member):
            with self.subTest(actor=actor.username):
                self.assertTrue(has_place_permission(user=actor, place=place, permission_code='place.edit'))
                with self.assertRaises(Http404):
                    serve_specialist_document(self.request(actor), self.document.pk)
