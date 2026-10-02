"""Stage 15 admin contracts: stale forms, candidate actions and role boundaries."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase

from catalog.domain_admin.place import PlaceAdmin
from catalog.models import Activity, OfferingGroup, Organization, Place, Program, VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place


class AdminEditorTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='admin15_owner')
        self.staff = get_user_model().objects.create_superuser(username='admin15_staff', email='staff15@example.invalid', password='synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        self.factory = RequestFactory()

    def test_place_carryover_is_not_submitted_as_hidden_mutable_input(self):
        editor = PlaceAdmin(Place, admin.site)
        request = self.factory.get('/admin/catalog/place/%s/change/' % self.place.pk)
        request.user = self.staff
        form = editor.get_form(request, self.place)(instance=self.place)
        from django.contrib.admin.helpers import AdminForm
        adminform = AdminForm(form, editor.get_fieldsets(request, self.place), {})
        carryover = editor._build_place_carryover_fields(adminform, [])
        self.assertEqual([field.name for field in carryover], ['publication_token'])

    def test_new_hierarchy_admin_is_registered(self):
        for model in (Organization, Program, Activity, OfferingGroup):
            self.assertIn(model, admin.site._registry)


    def test_organization_admin_draft_and_submit_use_candidate(self):
        from catalog.domain_admin.business import OrganizationAdmin, OrganizationForm
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Approved name')
        editor = OrganizationAdmin(Organization, admin.site)
        data = {
            'name_az': 'Candidate name', 'name_ru': '', 'name_en': '',
            'description_az': '', 'description_ru': '', 'description_en': '',
            'phone': '', 'whatsapp': '', 'website': '',
            'source_version': org.content_version, 'candidate_version': 0,
        }
        form = OrganizationForm(data=data, instance=org)
        self.assertTrue(form.is_valid(), str(form.errors))
        request = self.factory.post('/admin/catalog/organization/%s/change/' % org.pk, {**data, '_save_draft': '1'})
        request.user = self.staff
        editor.save_model(request, form.instance, form, True)
        org.refresh_from_db()
        self.assertEqual(org.name_az, 'Approved name')
        revision = VolunteerPlaceRevision.objects.get(organization=org)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.payload['name_az'], 'Candidate name')
        data['candidate_version'] = revision.version
        form = OrganizationForm(data=data, instance=org)
        self.assertTrue(form.is_valid(), str(form.errors))
        request = self.factory.post('/admin/catalog/organization/%s/change/' % org.pk, {**data, '_submit_candidate': '1'})
        request.user = self.staff
        editor.save_model(request, form.instance, form, True)
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')

    def test_other_staff_cannot_edit_organization_content(self):
        from catalog.domain_admin.business import OrganizationAdmin
        org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Owner content')
        editor = OrganizationAdmin(Organization, admin.site)
        request = self.factory.get('/admin/catalog/organization/%s/change/' % org.pk)
        request.user = self.staff
        self.assertFalse(editor.has_change_permission(request, org))
        self.assertTrue(editor.has_view_permission(request, org))

    def test_organization_change_renders_related_staff_link(self):
        from django.urls import reverse
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Admin organization')
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:catalog_organization_change', args=[org.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'catalog/organizationgrant/')
        self.assertContains(response, 'candidate_version')

    def test_program_activity_group_forms_render_without_direct_status_field(self):
        from django.urls import reverse
        from catalog.domain_admin.business import ActivityAdmin, OfferingGroupAdmin, ProgramAdmin
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Org')
        program = Program.objects.create(organization=org, created_by=self.staff, name_az='Program')
        Place.objects.filter(pk=self.place.pk).update(owner=self.staff)
        self.place.refresh_from_db()
        activity = Activity.objects.create(place=self.place, program=None, name_az='Activity')
        group = OfferingGroup.objects.create(activity=activity, name_az='Group')
        self.client.force_login(self.staff)
        for model, obj in ((Program, program), (Activity, activity), (OfferingGroup, group)):
            response = self.client.get(reverse('admin:catalog_%s_change' % model._meta.model_name, args=[obj.pk]))
            self.assertEqual(response.status_code, 200, model.__name__)
            self.assertContains(response, 'source_version')
            self.assertNotContains(response, 'name="status"')

    def test_organization_staff_invite_uses_owner_service(self):
        from django.urls import reverse
        from catalog.models import OrganizationTeamInvitation
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Team org')
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_organization_transition', args=[org.pk])
        response = self.client.post(url, {'action': 'invite', 'email': 'editor15@example.invalid'})
        self.assertEqual(response.status_code, 302)
        invite = OrganizationTeamInvitation.objects.get(organization=org)
        self.assertEqual(invite.email, 'editor15@example.invalid')
        self.assertEqual(invite.scope, 'all_network')
        self.assertEqual(invite.actions, ['organization.edit', 'organization.view', 'program.manage'])
        other = get_user_model().objects.create_superuser(username='admin15_otherstaff', email='otherstaff15@example.invalid', password='synthetic')
        self.client.force_login(other)
        response = self.client.post(url, {'action': 'invite', 'email': 'blocked15@example.invalid'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(OrganizationTeamInvitation.objects.filter(email='blocked15@example.invalid').exists())

    def test_pending_editor_shows_current_and_candidate_separately(self):
        from django.urls import reverse
        from catalog.services import publication
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Current')
        publication.propose(actor=self.staff, target_type='organization', target_id=org.pk,
                            patch={'name_az': 'Candidate'}, schema_version=publication.SCHEMA_VERSION,
                            expected_version=org.content_version, revision_version=0, submit=True)
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:catalog_organization_change', args=[org.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current')
        self.assertContains(response, 'Candidate')
        self.assertContains(response, 'km-pf-group')

    def test_staff_invite_error_does_not_create_record(self):
        from django.urls import reverse
        from catalog.models import OrganizationTeamInvitation
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Team org')
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:catalog_organization_transition', args=[org.pk]),
                                    {'action': 'invite', 'email': 'not-an-email'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(OrganizationTeamInvitation.objects.filter(organization=org).exists())

    def test_unpublish_service_uses_existing_reviewer_acl_and_version(self):
        from catalog.services.publication import unpublish
        old_name = self.place.name_az
        with self.assertRaises(ValidationError):
            unpublish(actor=self.staff, target_type='place', target_id=self.place.pk, expected_version=999)
        with self.assertRaises(PermissionDenied):
            unpublish(actor=self.owner, target_type='place', target_id=self.place.pk, expected_version=self.place.content_version)
        unpublish(actor=self.staff, target_type='place', target_id=self.place.pk, expected_version=self.place.content_version)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)
        self.assertEqual(self.place.name_az, old_name)

    def test_unpublish_refuses_pending_candidate(self):
        from catalog.services import publication
        revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
                                       patch={'description_az': 'Pending'}, schema_version=publication.SCHEMA_VERSION,
                                       expected_version=self.place.content_version, revision_version=0, submit=True)
        self.place.refresh_from_db()
        with self.assertRaises(ValidationError):
            publication.unpublish(actor=self.staff, target_type='place', target_id=self.place.pk,
                                  expected_version=self.place.content_version)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')

    def test_place_admin_unpublish_skips_form_save(self):
        from django.urls import reverse
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_change', args=[self.place.pk])
        response = self.client.post(url, {'_unpublish_place': '1', 'unpublish_version': self.place.content_version})
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_organization_admin_unpublish_uses_review_service(self):
        from django.urls import reverse
        from django.utils import timezone
        org = Organization.objects.create(owner=self.staff, created_by=self.staff, name_az='Published',
                                          status='published', approved_at=timezone.now())
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_organization_transition', args=[org.pk])
        response = self.client.post(url, {'action': 'unpublish', 'source_version': org.content_version})
        self.assertEqual(response.status_code, 302)
        org.refresh_from_db()
        self.assertEqual(org.status, 'draft')

    def test_activity_approval_and_unpublish_are_distinct(self):
        from catalog.services import publication
        activity = Activity.objects.create(place=self.place, name_az='Approved old')
        revision = publication.propose(actor=self.owner, target_type='activity', target_id=activity.pk,
                                       patch={'name_az': 'Approved new'}, schema_version=publication.SCHEMA_VERSION,
                                       expected_version=activity.content_version, revision_version=0, submit=True)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        activity.refresh_from_db()
        self.assertEqual(activity.name_az, 'Approved new')
        self.assertEqual(activity.status, 'published')
        publication.unpublish(actor=self.staff, target_type='activity', target_id=activity.pk,
                              expected_version=activity.content_version)
        activity.refresh_from_db()
        self.assertEqual(activity.status, 'draft')

    def test_group_badges_follow_activity_and_condition_confirmation(self):
        from catalog.domain_admin.business import OfferingGroupAdmin
        activity = Activity.objects.create(place=self.place, name_az='A', status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='G')
        editor = OfferingGroupAdmin(OfferingGroup, admin.site)
        self.assertIn(str(activity.get_status_display()), str(editor.publication_badge(group)))
        before = str(editor.verified_badge(group))
        from django.utils import timezone
        group.conditions_verified_at = timezone.now()
        self.assertNotEqual(before, str(editor.verified_badge(group)))

    def test_stale_concealed_place_value_cannot_overwrite_fresh_live_value(self):
        import json
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.services.place_schedule import serialize_place_schedule
        initial = PlaceAdminForm(instance=self.place)
        data = dict(initial.initial)
        data.update(pricing_plans=json.dumps(self.place.pricing_plans),
                    structured_schedule=json.dumps(serialize_place_schedule(self.place)),
                    extra_conditions='stale browser value', _save_draft='1')
        Place.objects.filter(pk=self.place.pk).update(extra_conditions='fresh independent value')
        form = PlaceAdminForm(data=data, instance=Place.objects.get(pk=self.place.pk))
        self.assertFalse(form.is_valid())
        self.assertIn('Publication source', str(form.errors))
        self.place.refresh_from_db()
        self.assertEqual(self.place.extra_conditions, 'fresh independent value')
