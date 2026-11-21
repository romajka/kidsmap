from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import OwnerTeamMembership, Place, PlaceOwnershipRequest, ServerDraft, VolunteerPlaceRevision
from catalog.services.owner_place_dashboard import project_owner_place
from catalog.services.pricing_plans import prefetch_place_pricing_records
from catalog.testcases.utils import create_quality_place


class OwnerPlacesPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('places-owner')
        cls.observer = get_user_model().objects.create_user('places-observer')
        cls.published = [
            create_quality_place(name_az=f'Published club {index}', owner=cls.owner, photo='')
            for index in range(15)
        ]
        # Equal modification times must not introduce duplicates at a page boundary.
        Place.objects.filter(pk__in=[place.pk for place in cls.published]).update(
            updated_at=cls.published[0].updated_at, rating_avg=4, rating_count=2, likes_count=1,
        )
        cls.draft = create_quality_place(owner=cls.owner, status='draft', is_active=False, photo='')
        cls.unavailable = create_quality_place(owner=cls.observer, photo='')

    def setUp(self):
        self.client.force_login(self.owner)
        with override('ru'):
            self.url = reverse('owner_places_dashboard')

    def test_later_page_limits_card_work_and_preserves_global_stats_and_navigation(self):
        oldest, empty, changed = self.published[:3]
        for place, status, payload in (
            (oldest, 'pending', {}), (empty, 'draft', {}), (changed, 'draft', {'name_ru': 'Saved'}),
        ):
            VolunteerPlaceRevision.objects.create(place=place, author=self.owner, status=status, payload=payload)
        for place in (empty, changed, self.unavailable):
            PlaceOwnershipRequest.objects.create(place=place, applicant=self.owner, request_kind='PUBLICATION')
        for index in range(13):
            ServerDraft.objects.create(actor=self.owner, target_type='place', fields={'name_az': f'Saved {index}'})

        newest_first = [place.pk for place in reversed(self.published)]
        first = self.client.get(self.url, {'draft_page': '2'})
        self.assertEqual(first.status_code, 200)
        self.assertEqual([place.pk for place in first.context['published_places']], newest_first[:12])
        self.assertEqual(first.context['pending_moderation_count'], 3)
        self.assertContains(first, 'href="?draft_page=2&amp;published_page=2#owner-places-list"')

        with (
            patch('catalog.services.owner_place_dashboard.project_owner_place', wraps=project_owner_place) as project,
            patch('catalog.services.pricing_plans.prefetch_place_pricing_records', wraps=prefetch_place_pricing_records) as prices,
        ):
            second = self.client.get(self.url, {'published_page': '2', 'draft_page': '2'})
        self.assertEqual(second.status_code, 200)
        self.assertEqual([place.pk for place in second.context['published_places']], newest_first[12:])
        self.assertEqual([place.pk for place in second.context['draft_places']], [self.draft.pk])
        self.assertEqual(second.context['latest_editable_place'].pk, self.draft.pk)
        self.assertEqual(second.context['working_drafts_count'], 13)
        self.assertEqual(len(second.context['working_drafts']), 1)
        self.assertEqual(second.context['owner_stats']['total_places'], 16)
        self.assertEqual(second.context['owner_stats']['published_places'], 15)
        self.assertEqual(second.context['owner_stats']['total_likes'], 15)
        self.assertEqual(second.context['owner_stats']['total_reviews'], 30)
        self.assertEqual(second.context['owner_stats']['avg_rating'], 4)
        self.assertEqual(second.context['pending_moderation_count'], 3)
        self.assertContains(second, 'href="?published_page=2&amp;draft_page=1#owner-working-drafts"')
        self.assertContains(second, 'data-place-id="', count=4)
        self.assertNotContains(second, f'data-place-id="{self.unavailable.pk}"')
        expected_projected = set(newest_first[12:] + [self.draft.pk])
        self.assertEqual({call.args[0].pk for call in project.call_args_list}, expected_projected)
        prices.assert_called_once()
        self.assertEqual({place.pk for place in prices.call_args.args[0]}, expected_projected)

    def test_observer_cannot_see_offpage_private_review_or_edit_link(self):
        for place in self.published:
            OwnerTeamMembership.objects.create(
                place=place, member=self.observer, owner=self.owner, role='MODERATOR',
                base_ownership_version=place.ownership_version,
            )
        place = self.published[0]
        VolunteerPlaceRevision.objects.create(place=place, author=self.owner, status='pending',
                                             payload={'name_ru': 'Private change'})
        self.client.force_login(self.observer)
        for page in ('bad', '999'):
            with self.subTest(page=page):
                response = self.client.get(self.url, {'published_page': page})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['pending_moderation_count'], 0)
                self.assertNotContains(response, 'Private change')
                self.assertNotContains(response, reverse('owner_place_edit', args=[place.pk]))
                self.assertEqual(response.context['published_places_page'].number, 1 if page == 'bad' else 2)

    def test_revocation_after_offpage_revision_read_hides_private_status_and_global_stats(self):
        # Keep only a view grant on each target when the pending counter reads its candidates.
        Place.objects.filter(pk=self.unavailable.pk).update(owner=self.owner)
        for place in self.published:
            OwnerTeamMembership.objects.create(place=place, member=self.observer, owner=self.owner, role='MANAGER')
        for place, status in zip(self.published[:3], ('pending', 'pending', 'rejected')):
            VolunteerPlaceRevision.objects.create(place=place, author=self.owner, status=status, payload={})
        PlaceOwnershipRequest.objects.create(place=self.published[2], applicant=self.observer, request_kind='PUBLICATION')
        self.client.force_login(self.observer)
        changed = False

        def revoke_after_read(execute, sql, params, many, context):
            nonlocal changed
            result = execute(sql, params, many, context)
            if not changed and sql.startswith(f'SELECT "{VolunteerPlaceRevision._meta.db_table}"."place_id"'):
                changed = True
                OwnerTeamMembership.objects.filter(member=self.observer).update(actions=['place.view'])
            return result

        with connection.execute_wrapper(revoke_after_read):
            response = self.client.get(self.url)
        self.assertTrue(changed)
        self.assertEqual(response.context['pending_moderation_count'], 1)
        self.assertFalse(response.context['can_view_stats'])
        self.assertFalse(response.context['can_edit_places'])
