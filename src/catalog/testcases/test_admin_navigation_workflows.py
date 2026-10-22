"""Authorized parent context survives navigation; GETs do not publish or create."""
from urllib.parse import parse_qs, urlsplit

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.domain_admin.business import ActivityAdmin, OfferingGroupAdmin
from catalog.models import Activity, OfferingGroup, Organization, Place, Program, VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place


class AdminNavigationWorkflowTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser(
            'navigation_owner', 'nav-owner@example.invalid', 'fictional'
        )
        self.other = get_user_model().objects.create_user('navigation_other')
        self.place = create_quality_place(owner=self.staff, created_by=self.staff, name_az='Synthetic owned centre')
        self.foreign = create_quality_place(owner=self.other, created_by=self.other, name_az='Synthetic foreign centre')
        self.activity = Activity.objects.create(place=self.place, name_az='Owned activity')
        self.foreign_activity = Activity.objects.create(place=self.foreign, name_az='Foreign activity')
        self.group = OfferingGroup.objects.create(activity=self.activity, name_az='Owned group')
        self.factory = RequestFactory()
        self.client.force_login(self.staff)

    def _request(self, url):
        request = self.factory.get(url)
        request.user = self.staff
        return request

    def _urls(self, links):
        return [link['url'] if isinstance(link, dict) else link[1] for link in links]

    def test_saved_place_links_to_its_activities_and_preselected_add(self):
        response = self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
        urls = self._urls(response.context.get('km_place_navigation', []))
        self.assertIn(reverse('admin:catalog_activity_changelist') + '?place__id__exact=%s' % self.place.pk, urls)
        self.assertIn(reverse('admin:catalog_activity_add') + '?place=%s' % self.place.pk, urls)
        for url in urls:
            self.assertNotIn(str(self.foreign.pk), parse_qs(urlsplit(url).query).get('place', []))

    def test_activity_links_back_to_own_place_and_forward_to_groups(self):
        response = self.client.get(reverse('admin:catalog_activity_change', args=[self.activity.pk]))
        self.assertEqual(response.status_code, 200)
        urls = self._urls(response.context.get('km_business_links', []))
        self.assertIn(reverse('admin:catalog_place_change', args=[self.place.pk]), urls)
        self.assertIn(reverse('admin:catalog_offeringgroup_changelist') + '?activity__id__exact=%s' % self.activity.pk, urls)
        self.assertIn(reverse('admin:catalog_offeringgroup_add') + '?activity=%s' % self.activity.pk, urls)
        self.assertIn(reverse('admin:catalog_place_change', args=[self.place.pk]) + '#pricing', urls)

    def test_group_links_back_to_activity_and_correct_place_pricing(self):
        response = self.client.get(reverse('admin:catalog_offeringgroup_change', args=[self.group.pk]))
        self.assertEqual(response.status_code, 200)
        urls = self._urls(response.context.get('km_business_links', []))
        self.assertIn(reverse('admin:catalog_activity_change', args=[self.activity.pk]), urls)
        self.assertIn(reverse('admin:catalog_place_change', args=[self.place.pk]) + '#pricing', urls)
        self.assertNotIn(reverse('admin:catalog_place_change', args=[self.foreign.pk]) + '#pricing', urls)

    def test_activity_add_preselects_only_editable_place(self):
        editor = ActivityAdmin(Activity, admin.site)
        for place, allowed in ((self.place, True), (self.foreign, False)):
            request = self._request(reverse('admin:catalog_activity_add') + '?place=%s' % place.pk)
            if allowed:
                initial = editor.get_changeform_initial_data(request)
                self.assertEqual(str(initial.get('place')), str(place.pk))
            else:
                with self.assertRaises(PermissionDenied):
                    editor.get_changeform_initial_data(request)

    def test_group_add_preselects_only_editable_activity(self):
        editor = OfferingGroupAdmin(OfferingGroup, admin.site)
        for activity, allowed in ((self.activity, True), (self.foreign_activity, False)):
            request = self._request(reverse('admin:catalog_offeringgroup_add') + '?activity=%s' % activity.pk)
            if allowed:
                initial = editor.get_changeform_initial_data(request)
                self.assertEqual(str(initial.get('activity')), str(activity.pk))
            else:
                with self.assertRaises(PermissionDenied):
                    editor.get_changeform_initial_data(request)

    def test_invalid_explicit_parent_hints_are_denied_without_lookup_errors(self):
        for model, editor, field in (
            ('activity', ActivityAdmin(Activity, admin.site), 'place'),
            ('offeringgroup', OfferingGroupAdmin(OfferingGroup, admin.site), 'activity'),
        ):
            for value in ('not-a-number', '999999999', '-1'):
                with self.subTest(model=model, value=value):
                    request = self._request(reverse('admin:catalog_%s_add' % model) + '?%s=%s' % (field, value))
                    with self.assertRaises(PermissionDenied):
                        editor.get_changeform_initial_data(request)

    def test_technical_hub_keeps_all_moved_classic_destinations(self):
        response = self.client.get(reverse('admin:kidsmap_navigation_technical'))
        self.assertEqual(response.status_code, 200)
        for model in ('program', 'activity', 'offeringgroup', 'organizationgrant'):
            self.assertContains(response, reverse('admin:catalog_%s_changelist' % model))
        # The hub only presents links; it must not render sensitive provider values.
        self.assertNotContains(response, 'name="secret"')
        self.assertNotContains(response, 'name="token"')

    def test_child_only_permission_keeps_activity_discoverable_without_place_permission(self):
        staff = get_user_model().objects.create_user('activity_only_staff', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='view_activity',
        ))
        self.assertFalse(staff.has_perm('catalog.view_place'))
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:kidsmap_navigation_technical'))
        self.assertContains(response, reverse('admin:catalog_activity_changelist'))
        for model in ('program', 'offeringgroup', 'organizationgrant'):
            self.assertNotContains(response, reverse('admin:catalog_%s_changelist' % model))
        request = self.factory.get(reverse('admin:index'))
        request.user = staff
        sections = admin.site.each_context(request)['kidsmap_sidebar_sections']
        urls = [item['url'] for section in sections for item in section['items']]
        self.assertIn(reverse('admin:kidsmap_navigation_technical'), urls)

    def test_directory_hub_lists_all_existing_directory_destinations(self):
        response = self.client.get(reverse('admin:kidsmap_navigation_directories'))
        self.assertEqual(response.status_code, 200)
        for model in ('category', 'subcategory', 'specialistspecialization', 'region', 'district', 'metrostation'):
            self.assertContains(response, reverse('admin:catalog_%s_changelist' % model))

    def test_directory_hub_filters_models_for_limited_staff(self):
        staff = get_user_model().objects.create_user('subcategory_only_staff', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_subcategory'))
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:kidsmap_navigation_directories'))
        self.assertContains(response, reverse('admin:catalog_subcategory_changelist'))
        for model in ('category', 'region', 'district', 'metrostation'):
            self.assertNotContains(response, reverse('admin:catalog_%s_changelist' % model))

    def test_region_only_staff_finds_region_under_geography_not_taxonomy(self):
        staff = get_user_model().objects.create_user('region_only_staff', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='view_region',
        ))
        self.client.force_login(staff)
        with override('ru'):
            response = self.client.get(reverse('admin:kidsmap_navigation_directories'))
        self.assertEqual(response.status_code, 200)
        groups = response.context['navigation_groups']
        region_url = reverse('admin:catalog_region_changelist')
        region_group = next(group for group in groups if any(
            item['url'] == region_url for item in group['items']))
        self.assertEqual(str(region_group['label']), 'Города, районы и метро')
        self.assertFalse(any(str(group['label']) == 'Категории и специализации' for group in groups))

    def test_business_editor_does_not_offer_place_links_without_place_access(self):
        staff = get_user_model().objects.create_user('activity_viewer_staff', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='view_activity',
        ))
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:catalog_activity_change', args=[self.foreign_activity.pk]))
        if response.status_code == 403:
            return
        self.assertEqual(response.status_code, 200)
        urls = self._urls(response.context.get('km_business_links', []))
        self.assertNotIn(reverse('admin:catalog_place_change', args=[self.foreign.pk]), urls)
        self.assertNotIn(reverse('admin:catalog_place_change', args=[self.foreign.pk]) + '#pricing', urls)

    def test_foreign_add_parent_is_denied_at_http_boundary_without_name_leak(self):
        for model, parent, field, foreign_name in (
            ('activity', self.foreign, 'place', 'Synthetic foreign centre'),
            ('offeringgroup', self.foreign_activity, 'activity', 'Foreign activity'),
        ):
            with self.subTest(model=model):
                url = reverse('admin:catalog_%s_add' % model) + '?%s=%s' % (field, parent.pk)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
                self.assertNotContains(response, foreign_name, status_code=403)

    def test_navigating_to_add_and_saving_draft_keeps_selected_parent(self):
        url = reverse('admin:catalog_activity_add') + '?place=%s' % self.place.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertEqual(str(form['place'].value()), str(self.place.pk))
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name in form.fields}
        data.update(name_az='Navigation draft activity', _save_draft='1')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        created = Activity.objects.exclude(pk__in=[self.activity.pk, self.foreign_activity.pk]).get()
        self.assertEqual(created.place_id, self.place.pk)
        self.assertEqual(created.status, 'draft')
        revision = VolunteerPlaceRevision.objects.get(activity=created)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.payload['name_az'], 'Navigation draft activity')
        self.assertEqual(response.url, reverse('admin:catalog_activity_change', args=[created.pk]))
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['adminform'].form['name_az'].value(), 'Navigation draft activity')

    def test_invalid_add_form_preserves_errors_without_creating_business_records(self):
        url = reverse('admin:catalog_activity_add') + '?place=%s' % self.place.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name in form.fields}
        data.update(place='invalid-parent', name_az='Invalid navigation draft', _save_draft='1')
        before = (Activity.objects.count(), VolunteerPlaceRevision.objects.count())
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('place', response.context['adminform'].form.errors)
        self.assertEqual((Activity.objects.count(), VolunteerPlaceRevision.objects.count()), before)

    def test_navigation_get_does_not_create_or_modify_business_records(self):
        models = (Organization, Program, Place, Activity, OfferingGroup, VolunteerPlaceRevision)
        before = {model: list(model.objects.order_by('pk').values()) for model in models}
        urls = [reverse('admin:kidsmap_navigation_%s' % name) for name in ('directories', 'technical')]
        urls.extend((
            reverse('admin:catalog_place_change', args=[self.place.pk]),
            reverse('admin:catalog_activity_change', args=[self.activity.pk]),
            reverse('admin:catalog_offeringgroup_change', args=[self.group.pk]),
            reverse('admin:catalog_activity_add') + '?place=%s' % self.place.pk,
            reverse('admin:catalog_offeringgroup_add') + '?activity=%s' % self.activity.pk,
        ))
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        for model in models:
            self.assertEqual(list(model.objects.order_by('pk').values()), before[model], model.__name__)
