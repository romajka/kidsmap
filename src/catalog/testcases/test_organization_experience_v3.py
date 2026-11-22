"""Organizations v3: one-click publish for staff, guided admin, public stats,
branch map data and mobile action bar. Positive and negative."""
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from catalog.models import Organization, Place, VolunteerPlaceRevision
from catalog.testcases.test_organization_lifecycle_v2 import OrganizationV2Base


class AdminPublishFlowTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        Organization.objects.filter(pk=self.org.pk).update(owner=self.staff)
        self.org.refresh_from_db()
        self.change = reverse('admin:catalog_organization_change', args=[self.org.pk])
        self.client.force_login(self.staff)
        self.client.cookies['django_language'] = 'ru'

    def post(self, user=None, **extra):
        self.org.refresh_from_db()
        revision = VolunteerPlaceRevision.objects.filter(organization=self.org).first()
        data = {'name_az': self.org.name_az, 'description_az': 'Uşaqlar üçün yaradıcılıq dərsləri',
                'source_version': self.org.content_version, 'candidate_version': revision.version if revision else 0, **extra}
        return self.client.post(self.change, data)

    def test_save_and_publish_makes_it_public_in_one_click(self):
        response = self.post(_save_and_publish='1')
        self.assertEqual(response.status_code, 302)
        self.org.refresh_from_db()
        self.assertTrue(self.org.is_public)
        self.assertEqual(self.org.slug, 'gunes-akademiyasi')
        self.assertEqual(self.client.get('/ru/organizations/gunes-akademiyasi/').status_code, 200)

    def test_save_draft_never_publishes(self):
        self.post(_save_draft='1')
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_public)
        self.assertEqual(VolunteerPlaceRevision.objects.get(organization=self.org).status, 'draft')

    def test_submit_for_review_waits_for_a_decision(self):
        self.post(_submit_candidate='1')
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_public)
        self.assertEqual(VolunteerPlaceRevision.objects.get(organization=self.org).status, 'pending')

    def test_staff_without_publish_right_gets_no_button_and_cannot_force_it(self):
        U = get_user_model()
        editor = U.objects.create_user('org_v3_editor', is_staff=True)
        editor.user_permissions.add(*Permission.objects.filter(codename__in=['view_organization', 'change_organization']))
        Organization.objects.filter(pk=self.org.pk).update(owner=editor)
        self.client.force_login(editor)
        page = self.client.get(self.change)
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'name="_save_and_publish"')
        self.assertContains(page, 'name="_submit_candidate"')
        self.post(_save_and_publish='1')
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_public)
        self.assertEqual(VolunteerPlaceRevision.objects.get(organization=self.org).status, 'pending')

    def test_change_form_explains_next_step_and_has_live_preview(self):
        page = self.client.get(self.change)
        self.assertContains(page, 'km-orgc-next')
        self.assertContains(page, 'data-org-preview')
        self.assertContains(page, 'kidsmap_organization_admin.js')
        self.assertContains(page, 'name="_save_and_publish"')

    def test_pending_state_points_to_the_decision(self):
        self.post(_submit_candidate='1')
        page = self.client.get(self.change)
        self.assertContains(page, 'href="#km-publication"')
        self.assertContains(page, 'id="km-publication"')

    def test_add_page_has_guide_and_grammatical_title(self):
        page = self.client.get(reverse('admin:catalog_organization_add'))
        self.assertContains(page, 'km-orgc--add')
        self.assertContains(page, 'Новая организация')
        self.assertNotContains(page, 'Добавить Организация')

    def test_add_and_publish_from_scratch(self):
        response = self.client.post(reverse('admin:catalog_organization_add'), {
            'name_az': 'Mavi Dalğa', 'description_az': 'Üzgüçülük', 'source_version': 0, 'candidate_version': 0,
            '_save_and_publish': '1'})
        self.assertEqual(response.status_code, 302)
        org = Organization.objects.get(name_az='Mavi Dalğa')
        self.assertTrue(org.is_public)

    def test_empty_name_is_rejected_and_nothing_is_published(self):
        response = self.post(name_az='', _save_and_publish='1')
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_public)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())


class PublicExperienceTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        self.publish()

    def test_stats_band_and_mobile_bar_render(self):
        page = self.client.get(f'/ru/organizations/{self.org.slug}/')
        self.assertContains(page, 'orgv-stats')
        self.assertContains(page, 'data-orgv-mbar')
        self.assertContains(page, 'organization_public.js')

    def test_map_points_only_for_branches_with_coordinates_and_are_escaped(self):
        place = self.linked_place(name='Filial <b>1</b>')
        Place.objects.filter(pk=place.pk).update(lat=40.4093, lng=49.8671, status='published')
        page = self.client.get(f'/ru/organizations/{self.org.slug}/')
        points = page.context['org_map_points']
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]['lat'], 40.4093)
        self.assertNotIn(b'Filial <b>1</b>', page.content.split(b'orgv-map-points')[1][:400])
        self.assertContains(page, 'id="orgv-map-points"')
        Place.objects.filter(pk=place.pk).update(lat=None, lng=None)
        page = self.client.get(f'/ru/organizations/{self.org.slug}/')
        self.assertEqual(page.context['org_map_points'], [])
        self.assertNotContains(page, 'data-orgv-map ')

    def test_rating_is_zero_safe_without_reviews(self):
        page = self.client.get(f'/ru/organizations/{self.org.slug}/')
        self.assertEqual(page.context['org_rating'], {'avg': 0.0, 'count': 0})
        self.assertContains(page, 'профиль проверен')

    def test_directory_loads_v3_motion_layer(self):
        page = self.client.get('/ru/organizations/')
        self.assertContains(page, 'organization_public_v3.css')


class PendingReviewGuardTests(OrganizationV2Base):
    def test_publish_button_hidden_while_changes_wait_for_review(self):
        # A pending candidate is decided in the publication block, not overwritten by a one-click save.
        Organization.objects.filter(pk=self.org.pk).update(owner=self.staff)
        self.propose({'description_az': 'Dəyişiklik'}, actor=self.staff)
        self.client.force_login(self.staff)
        page = self.client.get(reverse('admin:catalog_organization_change', args=[self.org.pk]))
        self.assertContains(page, 'name="_submit_candidate"')
        self.assertNotContains(page, 'name="_save_and_publish"')
        self.assertContains(page, 'value="approve"')


class AdminChangelistTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.client.cookies['django_language'] = 'ru'
        self.url = reverse('admin:catalog_organization_changelist')

    def test_row_shows_state_readiness_and_next_action_for_each_state(self):
        draft = self.org
        pending = Organization.objects.create(owner=self.owner, name_az='Pending Org')
        published = Organization.objects.create(owner=self.owner, name_az='Live Org')
        from catalog.services import publication
        publication.propose(actor=self.owner, target_type='organization', target_id=pending.pk, patch={'description_az': 'x'},
                            schema_version=publication.SCHEMA_VERSION, expected_version=pending.content_version, revision_version=0, submit=True)
        publication.propose(actor=self.owner, target_type='organization', target_id=published.pk, patch={'description_az': 'y'},
                            schema_version=publication.SCHEMA_VERSION, expected_version=published.content_version, revision_version=0, submit=True)
        rev = VolunteerPlaceRevision.objects.get(organization=published)
        publication.review(actor=self.staff, revision_id=rev.pk, version=rev.version, approve=True)
        page = self.client.get(self.url)
        content = page.content.decode()
        self.assertIn('data-org-state="draft"', content)
        self.assertIn('data-org-state="pending"', content)
        self.assertIn('data-org-state="published"', content)
        self.assertIn('km-orgl-ready', content)
        self.assertIn(f'/admin/catalog/organization/{pending.pk}/change/#km-publication', content)
        self.assertIn(f'/admin/catalog/organization/{draft.pk}/change/', content)
        self.assertIn('/organizations/live-org/', content)

    def test_hint_when_nothing_is_public_disappears_after_publication(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'km-orgl-hint')
        self.publish()
        page = self.client.get(self.url)
        self.assertNotContains(page, 'km-orgl-hint')

    def test_bulk_publish_still_refuses_unsubmitted_drafts(self):
        response = self.client.post(self.url, {'action': 'mark_published', '_selected_action': [self.org.pk]}, follow=True)
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_public)
        self.assertContains(response, 'Сначала отправьте сведения на проверку')

    def test_name_is_escaped_in_row(self):
        Organization.objects.filter(pk=self.org.pk).update(name_az='<img src=x onerror=alert(1)>')
        page = self.client.get(self.url)
        self.assertNotContains(page, '<img src=x onerror=alert(1)>')
