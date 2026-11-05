"""Place review counts must lead to the same actionable rows, once each."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.domain_admin import _get_sidebar_metrics
from catalog.models import Place, PlaceOwnershipRequest, VolunteerPlaceRevision
from catalog.services.moderation_queue import queue_rows
from catalog.templatetags.admin_dashboard_tags import get_dashboard_stats
from catalog.testcases.utils import create_quality_place


class PlaceModerationQueueCoherenceTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_superuser('queue_admin', 'queue@example.invalid', 'fictional')
        self.owner = users.objects.create_user('queue_owner')
        self.owned = self.place('Owned edit', owner=self.owner)
        self.unowned = self.place('Unowned edit', status='draft', is_active=False)
        self.both = self.place('Pending card and edit', status='pending', is_active=False)
        self.legacy = self.place('Legacy pending', status='pending', is_active=False)
        self.pending_revisions = [VolunteerPlaceRevision.objects.create(
            place=place, author=self.owner, status='pending', payload={'description_ru': 'Review this change'},
        ) for place in (self.owned, self.unowned, self.both)]
        for status in ('draft', 'approved', 'rejected', 'declined'):
            # A decided/unsent candidate takes precedence over an old card flag.
            place = self.place('Excluded ' + status, status='pending', is_active=False)
            VolunteerPlaceRevision.objects.create(place=place, author=self.owner, status=status)
        for field, value in [('deleted_at', timezone.now()), ('is_temporary', True)]:
            place = self.place('Excluded ' + field, **{field: value})
            VolunteerPlaceRevision.objects.create(place=place, author=self.owner, status='pending')
        self.claim_place = self.place('Stale ownership claim')
        self.claim = PlaceOwnershipRequest.objects.create(
            place=self.claim_place, applicant=self.owner, status='PENDING', request_kind='CLAIM',
            base_ownership_version=self.claim_place.ownership_version + 1,
        )
        self.expected_ids = {self.owned.pk, self.unowned.pk, self.both.pk, self.legacy.pk}
        self.client.force_login(self.admin)

    def place(self, name, **kwargs):
        return create_quality_place(name=name, name_az=name, with_subcategory=True, **kwargs)

    def request(self, user=None):
        request = RequestFactory().get('/admin/')
        request.user = user or self.admin
        return request

    def test_sidebar_counts_actionable_candidates_and_keeps_claims_separate(self):
        metrics = _get_sidebar_metrics(self.request())
        self.assertEqual(metrics['places_pending'], 4)
        self.assertEqual(metrics['ownership_pending'], 1)
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, 'PENDING')

    def test_overview_counts_the_same_places(self):
        self.assertEqual(get_dashboard_stats()['pending']['places'], 4)

    def test_sidebar_destination_reveals_every_counted_place_once(self):
        response = self.client.get(reverse('admin:index'))
        groups = response.context['kidsmap_sidebar_sections']
        url = reverse('admin:catalog_moderation_moderationplace_changelist')
        item = next(item for group in groups for item in group['items'] if item['url'] == url)
        self.assertEqual(item['badge_count'], 4)
        response = self.client.get(item['url'])
        self.assertEqual(response.status_code, 200)
        ids = [obj.pk for obj in response.context['cl'].result_list]
        self.assertEqual(set(ids), self.expected_ids)
        self.assertEqual(len(ids), 4)

    def test_sla_tracks_owned_and_unowned_candidates_once_without_legacy_claims(self):
        rows = queue_rows(self.admin, {'type': 'place'}, now=timezone.now())
        expected = {('place', self.legacy.pk)} | {('place_revision', rev.pk) for rev in self.pending_revisions}
        self.assertEqual({(row['kind'], row['id']) for row in rows}, expected)
        self.assertEqual(len(rows), 4)
        response = self.client.get(reverse('admin:moderation_sla'), {'type': 'place'})
        self.assertEqual(response.context['places_count'], 4)

    def test_place_only_reviewer_can_open_queue_but_unprivileged_staff_cannot(self):
        reviewer = get_user_model().objects.create_user('place_reviewer', is_staff=True)
        reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_place'))
        self.client.force_login(reviewer)
        response = self.client.get(reverse('admin:catalog_moderation_moderationplace_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({obj.pk for obj in response.context['cl'].result_list}, self.expected_ids)
        denied = get_user_model().objects.create_user('queue_denied', is_staff=True)
        self.client.force_login(denied)
        self.assertEqual(self.client.get(reverse('admin:catalog_moderation_moderationplace_changelist')).status_code, 403)
        self.assertEqual(queue_rows(denied, {'type': 'place'}, now=timezone.now()), [])


class PendingPublishedPlaceActionsTests(TestCase):
    def setUp(self):
        from catalog.services import publication
        from catalog.testcases.utils import create_ready_place
        self.admin = get_user_model().objects.create_superuser('pending_admin', 'pending@example.invalid', 'fictional')
        self.owner = get_user_model().objects.create_user('pending_owner')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner)
        self.revision = publication.propose(
            actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'name_az': 'Candidate visible in moderation'}, schema_version=1,
            expected_version=self.place.content_version, submit=True,
        )
        self.client.force_login(self.admin)

    def test_moderation_row_preview_opens_candidate_while_general_catalog_keeps_public_link(self):
        from django.contrib import admin
        from catalog.proxy_apps.catalog_moderation.models import ModerationPlace
        from django.utils.translation import override
        preview_url = reverse('admin:catalog_place_site_preview', args=[self.place.pk])
        with override('ru'):
            html = str(admin.site._registry[ModerationPlace].col_actions(self.place))
            self.assertIn('href="' + preview_url + '"', html)
            self.assertIn('title="Предпросмотр"', html)
            self.assertNotIn('title="Просмотр на сайте"', html)
            self.assertIn('href="' + self.place.get_absolute_url() + '"', str(admin.site._registry[Place].col_actions(self.place)))
        response = self.client.get(preview_url)
        self.assertContains(response, 'Candidate visible in moderation')
        self.place.refresh_from_db()
        self.revision.refresh_from_db()
        self.assertNotEqual(self.place.name_az, 'Candidate visible in moderation')
        self.assertEqual(self.revision.status, 'pending')

    def test_moderation_change_form_edits_pending_candidate(self):
        response = self.client.get(reverse('admin:catalog_moderation_moderationplace_change', args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['adminform'].form['name_az'].value(), 'Candidate visible in moderation')

    def test_moderation_bulk_approve_applies_candidate_and_removes_queue_row(self):
        url = reverse('admin:catalog_moderation_moderationplace_changelist')
        response = self.client.post(url, {'action': 'mark_published', '_selected_action': [str(self.place.pk)]})
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.revision.refresh_from_db()
        self.assertEqual(self.place.name_az, 'Candidate visible in moderation')
        self.assertTrue(self.place.is_public)
        self.assertEqual(self.revision.status, 'approved')
        self.assertEqual(self.revision.reviewed_by_id, self.admin.pk)
        self.assertEqual(self.client.get(url).context['cl'].result_count, 0)
