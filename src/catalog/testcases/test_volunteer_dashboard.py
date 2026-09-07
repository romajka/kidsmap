from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.services.volunteer_places import content_snapshot
from catalog.testcases.utils import create_ready_place

User = get_user_model()


class VolunteerDashboardTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name=VOLUNTEER_GROUP)
        self.a = User.objects.create_user('alice', is_staff=True)
        self.b = User.objects.create_user('bob', is_staff=True)
        self.a.groups.add(group)
        self.b.groups.add(group)
        self.pa = create_ready_place(created_by=self.a, name_az='Alice center')
        self.pb = create_ready_place(created_by=self.b, name_az='Bob secret center', status='draft', is_active=False)
        self.client.force_login(self.a)

    def proposal(self, place, status='draft', **payload):
        return VolunteerPlaceRevision.objects.create(place=place, author=place.created_by, status=status,
            payload={**content_snapshot(place), **payload}, review_note='Уточните адрес' if status=='rejected' else '')

    def test_counts_search_and_filter_are_scoped_to_current_volunteer(self):
        self.proposal(self.pa, 'pending', name_az='Alice proposed center')
        self.proposal(self.pb, 'rejected')
        response = self.client.get('/admin/volunteer/')
        self.assertEqual(response.context['counts']['all'], 1)
        self.assertEqual(response.context['counts']['pending'], 1)
        self.assertEqual(response.context['counts']['published'], 0)
        self.assertNotContains(response, 'Bob secret')
        response = self.client.get('/admin/volunteer/', {'q':'Bob'})
        self.assertEqual(response.context['page'].paginator.count, 0)
        self.assertEqual(response.context['counts']['all'], 1)
        self.client.force_login(self.b)
        response = self.client.get('/admin/volunteer/', {'status':'rejected'})
        self.assertEqual([p.pk for p in response.context['page']], [self.pb.pk])
        self.assertNotContains(response, 'Alice center')

    def test_preview_uses_proposal_and_canonical_readiness(self):
        self.proposal(self.pa, 'rejected', name_az='Proposed title', address='')
        response = self.client.get(f'/admin/volunteer/{self.pa.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['card']['name'], 'Proposed title')
        self.assertContains(response, 'Уточните адрес')
        self.assertFalse(response.context['card']['readiness'].is_ready)
        self.pa.refresh_from_db()
        self.assertNotEqual(self.pa.address, '')

    def test_all_foreign_object_methods_and_ajax_are_denied(self):
        for prefix in ('', '/ru', '/en'):
            for route in (f'{self.pb.pk}/', f'{self.pb.pk}/edit/', f'{self.pb.pk}/photo/main/'):
                for method in (self.client.get,self.client.post):
                    response = method(f'{prefix}/admin/volunteer/{route}', {'place_id':self.pa.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertEqual(response.status_code,404)
        for route in (f'/admin/catalog/place/{self.pb.pk}/delete/', '/admin/catalog/place/', '/admin/autocomplete/'):
            self.assertEqual(self.client.post(route, {'action':'delete_selected','_selected_action':[self.pb.pk]}).status_code,403)
        self.assertTrue(Place.objects.filter(pk=self.pb.pk,deleted_at__isnull=True).exists())

    def test_foreign_private_place_not_disclosed_by_public_apis(self):
        self.assertEqual(self.client.get(reverse('place_pricing_api',args=[self.pb.slug])).status_code,404)
        self.assertEqual(self.client.post(reverse('place_phone_reveal',args=[self.pb.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('place_detail_legacy',args=[self.pb.pk])).status_code,404)

    def test_owner_photo_routes_cannot_bypass_proposal(self):
        for name,args in [('owner_photo_thumbnail',[self.pb.pk,0]),('owner_photo_edit_save',[self.pb.pk]),('owner_photo_create_save',[]),('owner_photo_prepare',[])]:
            for method in (self.client.get,self.client.post):
                self.assertEqual(method(reverse(name,args=args)).status_code,403)

    def test_dashboard_never_counts_deleted_temporary_or_handed_over_places(self):
        create_ready_place(created_by=self.a,deleted_at=timezone.now())
        create_ready_place(created_by=self.a,is_temporary=True)
        create_ready_place(created_by=self.a,owner=self.b)
        response=self.client.get('/admin/volunteer/')
        self.assertEqual(response.context['counts']['all'],1)

    def test_superadmin_retains_access_to_both_places(self):
        root=User.objects.create_superuser('root','root@example.test','test-pass')
        self.client.force_login(root)
        response=self.client.get(reverse('admin:catalog_place_changelist'))
        ids=set(response.context['cl'].queryset.values_list('pk',flat=True))
        self.assertTrue({self.pa.pk,self.pb.pk}.issubset(ids))

    def test_dashboard_private_no_cache_and_no_global_navigation(self):
        self.a.user_permissions.set(Permission.objects.all())
        response=self.client.get('/admin/volunteer/')
        self.assertIn('no-store',response.headers['Cache-Control'])
        for route in ('/admin/catalog/place/','/admin/catalog/staffaccessuser/','/admin/catalog/sitesettings/'):
            self.assertNotContains(response,f'href="{route}"')

    def test_empty_dashboard_and_no_search_results_are_distinct(self):
        self.pa.delete()
        response=self.client.get('/admin/volunteer/')
        self.assertTrue(response.context['is_empty'])
        create_ready_place(created_by=self.a)
        response=self.client.get('/admin/volunteer/',{'q':'no-match'})
        self.assertFalse(response.context['is_empty'])
        self.assertEqual(response.context['page'].paginator.count,0)

    def test_admin_place_form_has_restricted_actions_and_complete_fields(self):
        response=self.client.get('/admin/volunteer/add/')
        self.assertTemplateUsed(response,'admin/volunteer/place_form.html')
        for forbidden in ('owner_photo_prepare','name="owner"','name="is_superuser"','name="is_verified"','data-pw-delete'):
            self.assertNotContains(response,forbidden)
        self.assertContains(response, 'data-volunteer-admin-form')
        self.assertContains(response, 'data-volunteer-guide')
        self.assertEqual(len(response.context['volunteer_sections']), 5)
        import re
        from catalog.volunteer_forms import CONTENT_FIELDS
        names = re.findall(r'name="([^"]+)"', response.content.decode())
        for name in (*CONTENT_FIELDS, 'pricing_plans', 'structured_schedule', 'revision_version', 'base_token'):
            self.assertEqual(names.count(name), 1, name)
        for forbidden in ('name="_publish_place"', 'name="status"', 'data-duplicate-candidates-url', 'data-place-json-import-dialog'):
            self.assertNotContains(response, forbidden)

    def test_photo_route_is_private_and_checks_ownership_before_storage(self):
        from django.core.files.base import ContentFile
        self.pa.photo.save('own.png', ContentFile(b'private image bytes'))
        response=self.client.get(f'/admin/volunteer/{self.pa.pk}/photo/main/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(b''.join(response.streaming_content),b'private image bytes')
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(f'/admin/volunteer/{self.pa.pk}/photo/main/').status_code,404)

    def test_pagination_and_unpublished_fallback_state(self):
        for i in range(13):
            create_ready_place(created_by=self.a,name_az=f'Club number {i}',is_active=False)
        response=self.client.get('/admin/volunteer/',{'status':'unpublished','page':'2'})
        self.assertEqual(response.context['page'].paginator.count,13)
        self.assertEqual(len(response.context['cards']),1)
        self.assertEqual(response.context['cards'][0]['state'],'unpublished')

    def test_existing_place_post_cannot_spoof_admin_or_author_fields(self):
        from django import forms
        url=f'/admin/volunteer/{self.pa.pk}/edit/'
        form=self.client.get(url).context['form']
        data={name:form[name].value() if form[name].value() is not None else '' for name,field in form.fields.items() if not isinstance(field,forms.FileField)}
        data.update(action='draft',name_az='Alice changed',owner=self.b.pk,created_by=self.b.pk,
                    is_verified='on',is_recommended='on',status='published',is_active='on',deleted_at='2026-01-01')
        response=self.client.post(url,data)
        self.assertEqual(response.status_code,302)
        self.pa.refresh_from_db()
        self.assertEqual(self.pa.created_by_id,self.a.pk)
        self.assertIsNone(self.pa.owner_id)
        self.assertIsNone(self.pa.deleted_at)
        self.assertFalse(self.pa.is_verified)
        self.assertEqual(self.pa.name_az,'Alice center')
        proposal=self.pa.volunteer_revision
        self.assertEqual(proposal.status,'draft')
        for name in ('owner','created_by','is_verified','is_recommended','status','is_active','deleted_at'):
            self.assertNotIn(name,proposal.payload)

    def test_feedback_survives_saving_corrections_as_draft(self):
        from django import forms
        self.proposal(self.pa,'rejected')
        url=f'/admin/volunteer/{self.pa.pk}/edit/'
        form=self.client.get(url).context['form']
        data={name:form[name].value() if form[name].value() is not None else '' for name,field in form.fields.items() if not isinstance(field,forms.FileField)}
        data.update(action='draft',address='New corrected address')
        # Use the actual original snapshot, as a reviewer would.
        from catalog.services.volunteer_places import live_snapshot
        revision=self.pa.volunteer_revision
        revision.base_snapshot=live_snapshot(self.pa)
        revision.save()
        response=self.client.post(url,data)
        self.assertEqual(response.status_code,302)
        revision.refresh_from_db()
        self.assertEqual(revision.review_note,'Уточните адрес')
        response=self.client.get(f'/admin/volunteer/{self.pa.pk}/')
        self.assertContains(response,'Уточните адрес')
