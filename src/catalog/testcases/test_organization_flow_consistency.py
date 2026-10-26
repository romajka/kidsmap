"""Organization status, publishing and error recovery must agree across entry points."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import override

from catalog.domain_admin.business import OrganizationForm
from catalog.models import Organization
from catalog.services import organization_ownership, publication
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory


class OrganizationFlowConsistencyTests(TestCase):
    def setUp(self):
        ensure_quality_subcategory('EDU')
        U = get_user_model()
        self.owner = U.objects.create_user('org_flow_owner')
        self.staff = U.objects.create_superuser('org_flow_staff', 'flow@example.invalid', 'synthetic')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Flow network')
        self.model_admin = admin.site._registry[Organization]

    def candidate(self, submit=True):
        return publication.propose(actor=self.owner, target_type='organization', target_id=self.org.pk,
            patch={'description_az': 'Creative lessons for children'}, schema_version=publication.SCHEMA_VERSION,
            expected_version=self.org.content_version, revision_version=0, submit=submit)

    def action(self, name, actor=None, queryset=None):
        request = RequestFactory().post('/admin/catalog/organization/')
        request.user = actor or self.staff
        request.session = {}
        request._messages = FallbackStorage(request)
        getattr(self.model_admin, name)(request, queryset if queryset is not None else Organization.objects.filter(pk=self.org.pk))
        return [str(message) for message in request._messages]

    def test_two_branches_do_not_multiply_dashboard_totals(self):
        Organization.objects.create(owner=self.owner, name_az='Other network')
        for name in ('First branch', 'Second branch'):
            place = create_quality_place(owner=self.owner, created_by=self.owner, name=name)
            organization_ownership.request_join(actor=self.owner, place_id=place.pk, organization_id=self.org.pk)
        counts = self.model_admin._dashboard_counts()
        self.assertEqual(counts['total'], 2)
        self.assertEqual(counts['draft'], 2)
        self.assertEqual(counts['with_places'], 1)

    def test_pending_revision_is_in_queue_without_changing_base_status(self):
        self.candidate()
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'draft')
        self.assertEqual(self.model_admin._dashboard_counts()['pending'], 1)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:catalog_organization_changelist'), {'status': 'pending'})
        self.assertEqual(list(response.context['cl'].queryset.values_list('pk', flat=True)), [self.org.pk])

    def test_published_with_pending_changes_is_visible_in_both_filters(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=timezone.now())
        self.org.refresh_from_db()
        self.candidate()
        counts = self.model_admin._dashboard_counts()
        self.assertEqual((counts['published'], counts['pending'], counts['draft']), (1, 1, 0))

    def test_bulk_publication_cannot_claim_unsubmitted_draft_is_published(self):
        self.candidate(submit=False)
        messages = self.action('mark_published')
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'draft')
        self.assertIsNone(self.org.approved_at)
        self.assertTrue(messages)

    def test_bulk_pending_approval_uses_publication_service_and_is_public(self):
        self.candidate()
        self.action('mark_published')
        self.org.refresh_from_db()
        self.assertEqual(self.org.content_revision.status, 'approved')
        self.assertIsNotNone(self.org.approved_at)
        self.assertEqual(self.org.description_az, 'Creative lessons for children')
        self.assertEqual(self.client.get(reverse('organization_detail', args=[self.org.public_id])).status_code, 200)

    def test_bulk_cannot_bypass_reviewer_permission(self):
        actor = get_user_model().objects.create_user('org_flow_limited', is_staff=True)
        actor.user_permissions.add(Permission.objects.get(codename='change_organization'))
        self.candidate()
        self.action('mark_published', actor=actor)
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'draft')
        self.assertEqual(self.org.content_revision.status, 'pending')

    def test_bulk_unpublish_does_not_discard_pending_candidate(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=timezone.now())
        self.org.refresh_from_db()
        self.candidate()
        self.action('mark_draft')
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'published')
        self.assertEqual(self.org.content_revision.status, 'pending')

    def test_bulk_unpublish_approved_organization_removes_public_visibility(self):
        self.candidate()
        self.action('mark_published')
        self.action('mark_draft')
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'draft')
        self.assertEqual(self.client.get(reverse('organization_detail', args=[self.org.public_id])).status_code, 404)

    def test_mixed_bulk_does_not_publish_archived_or_unsubmitted_organization(self):
        self.candidate()
        archived = Organization.objects.create(owner=self.owner, name_az='Archived flow', archived_at=timezone.now())
        draft = Organization.objects.create(owner=self.owner, name_az='Unsubmitted flow')
        self.action('mark_published', queryset=Organization.objects.filter(pk__in=[self.org.pk, archived.pk, draft.pk]))
        self.org.refresh_from_db()
        archived.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual((self.org.status, archived.status, draft.status), ('published', 'draft', 'draft'))

    def test_bulk_source_conflict_keeps_candidate_pending_and_live_unchanged(self):
        self.candidate()
        Organization.objects.filter(pk=self.org.pk).update(description_az='Changed in another session')
        self.action('mark_published')
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'draft')
        self.assertEqual(self.org.description_az, 'Changed in another session')
        self.assertEqual(self.org.content_revision.status, 'pending')

    def test_archived_pending_revision_does_not_appear_in_active_queue(self):
        self.candidate()
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.assertEqual(self.model_admin._dashboard_counts()['pending'], 0)

    def test_owner_index_does_not_claim_unapproved_status_is_public(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/organizations/')
        self.assertNotContains(response, 'org-status-chip--published')

    def test_public_and_unpublished_badges_have_different_text_in_every_language(self):
        for language in ('ru', 'az', 'en'):
            with override(language), self.subTest(language=language):
                self.org.status = 'draft'
                self.org.approved_at = None
                unpublished = strip_tags(str(self.model_admin.publication_badge(self.org)))
                self.org.status = 'published'
                self.org.approved_at = timezone.now()
                published = strip_tags(str(self.model_admin.publication_badge(self.org)))
                self.assertNotEqual(unpublished, published)

    def test_successful_profile_submission_returns_to_profile_section(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('organization_workspace_save', args=[self.org.pk]),
            {'name_az': self.org.name_az, 'expected_version': self.org.content_version,
             'revision_version': 0, 'submit': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('#org-about'))

    def test_admin_missing_az_is_a_bound_field_error_preserving_ru(self):
        self.assertTrue(OrganizationForm().fields['name_az'].required)
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:catalog_organization_add'),
            {'name_az': '', 'name_ru': 'Keep this input', 'candidate_version': 0, 'source_version': 0, '_save': '1'})
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertIn('name_az', form.errors)
        self.assertEqual(form['name_ru'].value(), 'Keep this input')

    def test_admin_service_error_preserves_duplicate_input(self):
        self.org.owner = self.staff
        self.org.save(update_fields=['owner'])
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:catalog_organization_add'),
            {'name_az': self.org.name_az, 'name_ru': 'Keep duplicate input', 'candidate_version': 0, 'source_version': 0, '_save': '1'})
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertTrue(form.errors)
        self.assertEqual(form['name_ru'].value(), 'Keep duplicate input')

    def test_owner_create_invalid_phone_is_field_error_and_creates_nothing(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('organization_workspace_create'),
            {'name_az': 'Bad contact network', 'phone': 'not-a-phone'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.context['create_form'].errors)
        self.assertEqual(response.context['create_form']['name_az'].value(), 'Bad contact network')
        self.assertFalse(Organization.objects.filter(name_az='Bad contact network').exists())

    def test_service_create_rejects_invalid_phone_independently_of_forms(self):
        with self.assertRaises(ValidationError):
            organization_ownership.create_organization(actor=self.owner,
                values={'name_az': 'Bad service contact', 'phone': 'not-a-phone'})
        self.assertFalse(Organization.objects.filter(name_az='Bad service contact').exists())

    def test_owner_edit_invalid_phone_identifies_field(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('organization_workspace_save', args=[self.org.pk]),
            {'name_az': 'Retain input', 'phone': 'not-a-phone', 'expected_version': self.org.content_version,
             'revision_version': 0, 'submit': '1'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.context['candidate_form'].errors)
        self.assertEqual(response.context['candidate_form']['name_az'].value(), 'Retain input')

    def test_service_create_normalizes_international_contact_without_truncation(self):
        org = organization_ownership.create_organization(actor=self.owner,
            values={'name_az': 'International network', 'phone': '+1 310 456 4918'})
        self.assertEqual(org.phone, '+13104564918')

    def test_standalone_place_is_not_described_as_stale_affiliation(self):
        create_quality_place(owner=self.owner, created_by=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/organizations/')
        self.assertNotContains(response, 'Связь неактуальна')

    def test_phone_alone_does_not_advertise_whatsapp_for_organization(self):
        from catalog.services.public_presentation import contact_data
        self.org.status = 'published'
        self.org.approved_at = timezone.now()
        self.org.phone = '+994501112233'
        self.org.save()
        self.assertTrue(contact_data(self.org)['has_phone'])
        self.assertFalse(contact_data(self.org)['has_whatsapp'])

    def test_explicit_same_phone_choice_saves_whatsapp(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('organization_workspace_create'),
            {'name_az': 'Explicit WhatsApp network', 'phone': '+994501112233', 'whatsapp_same_as_phone': 'on'})
        self.assertEqual(response.status_code, 302)
        org = Organization.objects.get(name_az='Explicit WhatsApp network')
        self.assertEqual(org.whatsapp, '+994501112233')

    def test_second_owner_can_preview_names_without_confirming_affiliation(self):
        other = get_user_model().objects.create_user('org_flow_other_owner')
        place = create_quality_place(owner=other, created_by=other, name_az='Specific external branch')
        item = organization_ownership.request_join(actor=self.owner, place_id=place.pk, organization_id=self.org.pk)
        self.client.force_login(other)
        url = reverse('organization_confirm_preview', args=[self.org.pk, item.pk])
        response = self.client.get(url)
        self.assertContains(response, self.org.name_az)
        self.assertContains(response, place.name_az)
        item.refresh_from_db()
        self.assertIsNone(item.place_owner_confirmed_at)
        stranger = get_user_model().objects.create_user('org_flow_stranger')
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(url).status_code, 404)
