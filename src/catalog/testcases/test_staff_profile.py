from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Place, VolunteerPlaceRevision
from catalog.testcases.utils import create_ready_place
from catalog.services.staff_roles import VOLUNTEER_GROUP

User = get_user_model()


class StaffProfileTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser('reviewer', 'root@example.test', 'test-password')
        self.volunteer = User.objects.create_user('volunteer', is_staff=True)
        self.volunteer.groups.add(Group.objects.create(name=VOLUNTEER_GROUP))
        self.client.force_login(self.root)
        self.url = reverse('admin:catalog_staffaccessuser_change', args=[self.volunteer.pk])

    def test_list_counts_creation_not_ownership_and_filters_volunteers(self):
        create_ready_place(created_by=self.volunteer)
        create_ready_place(owner=self.volunteer, created_by=self.root)
        response = self.client.get(reverse('admin:catalog_staffaccessuser_changelist'), {'role': 'volunteer'})
        rows = list(response.context['cl'].result_list)
        self.assertEqual([row.pk for row in rows], [self.volunteer.pk])
        self.assertEqual(rows[0].places_count, 1)
        self.assertContains(response, 'Волонтёр')

    def test_statistics_keep_live_place_and_revision_status_separate(self):
        live = create_ready_place(created_by=self.volunteer)
        create_ready_place(created_by=self.volunteer, status=Place.STATUS_DRAFT, is_active=False)
        create_ready_place(created_by=self.volunteer, deleted_at=timezone.now())
        create_ready_place(owner=self.volunteer, created_by=self.root)
        VolunteerPlaceRevision.objects.create(place=live, author=self.volunteer, status='pending')
        response = self.client.get(self.url)
        stats = response.context['staff_stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['published'], 1)
        self.assertEqual(stats['draft'], 1)
        self.assertEqual(stats['deleted'], 1)
        self.assertEqual(stats['revision_pending'], 1)
        response = self.client.get(self.url, {'place_state': 'revision_pending'})
        self.assertEqual([p.pk for p in response.context['staff_places']], [live.pk])

    def form_data(self):
        response = self.client.get(self.url)
        form = response.context['adminform'].form
        data = {}
        for name in form.fields:
            value = form[name].value()
            if value not in (None, False):
                data[name] = value
        for inline in response.context['inline_admin_formsets']:
            formset = inline.formset
            for field in formset.management_form:
                data[field.html_name] = field.value()
            for child in formset.forms:
                for field in child:
                    if field.value() is not None:
                        data[field.html_name] = field.value()
        return data

    def test_profile_edit_preserves_role_and_saves_inactive(self):
        data = self.form_data()
        data.pop('is_active', None)
        data.update(first_name='Edited', _continue='1')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.volunteer.refresh_from_db()
        self.assertFalse(self.volunteer.is_active)
        self.assertFalse(self.volunteer.is_superuser)
        self.assertEqual(self.volunteer.first_name, 'Edited')
        self.assertTrue(self.volunteer.groups.filter(name=VOLUNTEER_GROUP).exists())

    def test_staff_cannot_forge_privilege_fields(self):
        staff = User.objects.create_user('editor', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_staffaccessuser'))
        self.client.force_login(staff)
        data = self.form_data()
        data.update(is_superuser='on', groups=[], user_permissions=list(Permission.objects.values_list('pk', flat=True)))
        response = self.client.post(self.url, data)
        self.assertIn(response.status_code, (200, 302, 403))
        self.volunteer.refresh_from_db()
        self.assertFalse(self.volunteer.is_superuser)
        self.assertEqual(self.volunteer.user_permissions.count(), 0)
        self.assertTrue(self.volunteer.groups.filter(name=VOLUNTEER_GROUP).exists())

    def test_pagination_search_and_other_creator_isolation(self):
        for i in range(17):
            create_ready_place(created_by=self.volunteer, name_az=f'Unique center {i}')
        other = create_ready_place(created_by=self.root, name_az='Other creator')
        response = self.client.get(self.url, {'place_page': 2, 'place_q': 'Unique'})
        self.assertEqual(len(response.context['staff_places']), 2)
        self.assertEqual(response.context['staff_places'].paginator.count, 17)
        self.assertNotIn(other.pk, [p.pk for p in response.context['staff_places']])

    def test_view_only_staff_gets_no_place_edit_links_or_save_button(self):
        viewer = User.objects.create_user('viewer', is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename='view_staffaccessuser'))
        create_ready_place(created_by=self.volunteer)
        self.client.force_login(viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['staff_places'][0].staff_change_url, '')
        self.assertNotContains(response, 'name="_continue"')
        self.assertEqual(self.client.post(self.url, {'first_name': 'forged'}).status_code, 403)

    def test_non_superuser_cannot_change_superuser_or_password(self):
        editor = User.objects.create_user('editor', is_staff=True)
        editor.user_permissions.add(Permission.objects.get(codename='change_staffaccessuser'))
        self.client.force_login(editor)
        for suffix in ('change', 'password_change'):
            url = reverse(f'admin:catalog_staffaccessuser_{suffix}', args=[self.root.pk])
            self.assertEqual(self.client.post(url, {'is_superuser': '', 'password1': 'New-pass-123!', 'password2': 'New-pass-123!'}).status_code, 403)

    def test_staff_profile_honors_azerbaijani_language_choice(self):
        from django.conf import settings
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'az'
        response = self.client.get(self.url)
        self.assertContains(response, 'Məkanlar və statistika')
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, 'az')
