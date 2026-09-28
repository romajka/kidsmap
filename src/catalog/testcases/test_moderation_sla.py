from datetime import timedelta

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from catalog.services.moderation_sla import calculate_sla


@override_settings(
    MODERATION_SLA={
        "place": {"hours": 72, "warning_percent": 50, "critical_percent": 80},
        "review": {"hours": 24, "warning_percent": 50, "critical_percent": 80},
    }
)
class ModerationSlaTests(SimpleTestCase):
    def setUp(self):
        self.now = timezone.now()

    def test_place_moves_from_fresh_to_warning_critical_and_breached(self):
        submitted = self.now - timedelta(hours=36)
        self.assertEqual(calculate_sla("place", submitted, now=self.now).status, "warning")
        self.assertEqual(calculate_sla("place", self.now - timedelta(hours=58), now=self.now).status, "critical")
        self.assertEqual(calculate_sla("place", self.now - timedelta(hours=72), now=self.now).status, "breached")

    def test_needs_changes_pauses_sla_without_deadline(self):
        result = calculate_sla("review", self.now - timedelta(hours=30), paused_at=self.now - timedelta(hours=2), now=self.now)
        self.assertEqual(result.status, "paused")
        self.assertIsNone(result.deadline)
        self.assertEqual(result.elapsed_seconds, 28 * 3600)

    @override_settings(MODERATION_SLA=[])
    def test_invalid_policy_container_is_rejected_cleanly(self):
        with self.assertRaises(ValueError):
            calculate_sla('place', self.now, now=self.now)

    def test_unknown_content_type_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_sla("event", self.now, now=self.now)

    def test_missing_submission_does_not_crash_or_invent_deadline(self):
        result = calculate_sla('place', None, now=self.now)
        self.assertEqual(result.status, 'unknown')
        self.assertIsNone(result.deadline)

    def test_thresholds_are_exact_and_not_rounded_early(self):
        self.assertEqual(calculate_sla('place', self.now - timedelta(hours=57, minutes=35, seconds=59), now=self.now).status, 'warning')
        self.assertEqual(calculate_sla('place', self.now - timedelta(hours=57, minutes=36), now=self.now).status, 'critical')


class ModerationLifecycleTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from catalog.models import Place
        self.admin = get_user_model().objects.create_superuser('sla-admin', 'sla@example.test', 'local-only')
        self.place = Place.objects.create(name='SLA Museum', category='EDU', status='pending', is_active=False)

    def test_place_submission_pause_and_resubmission_dates(self):
        self.assertIsNotNone(self.place.submitted_at)
        original = self.place.submitted_at
        self.place.address = 'Changed while pending'
        self.place.save(update_fields=['address'])
        self.place.refresh_from_db()
        self.assertEqual(self.place.submitted_at, original)
        self.place.status = 'needs_changes'
        self.place.rejection_reason = 'Please check the entrance'
        self.place.save(update_fields=['status', 'rejection_reason'])
        self.place.refresh_from_db()
        self.assertIsNotNone(self.place.needs_changes_at)
        self.place.status = 'pending'
        self.place.save(update_fields=['status'])
        self.place.refresh_from_db()
        self.assertGreater(self.place.submitted_at, original)
        self.assertIsNone(self.place.needs_changes_at)

    def test_pending_reviews_and_revision_get_submission_dates(self):
        from catalog.models import PlaceReview, SiteReview, VolunteerPlaceRevision
        for obj in (PlaceReview.objects.create(place=self.place, text='Good place', status='pending'),
                    SiteReview.objects.create(text='Good catalogue', status='pending'),
                    VolunteerPlaceRevision.objects.create(place=self.place, author=self.admin, status='pending')):
            self.assertIsNotNone(getattr(obj, 'submitted_at', None))

    def test_review_decision_tracks_date_and_actor(self):
        from catalog.models import PlaceReview
        review = PlaceReview.objects.create(place=self.place, text='Good place', status='pending')
        self.client.force_login(self.admin)
        from django.urls import reverse
        response = self.client.post(reverse('admin:catalog_placereview_approve', args=[review.pk]))
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertIsNotNone(review.moderated_at)
        self.assertEqual(review.moderated_by_id, self.admin.pk)

    def test_queue_is_staff_permission_scoped_and_oldest_first(self):
        from catalog.models import PlaceReview
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission, Group
        oldest = timezone.now() - timedelta(hours=80)
        type(self.place).objects.filter(pk=self.place.pk).update(submitted_at=oldest)
        PlaceReview.objects.create(place=self.place, text='Pending review', status='pending')
        self.client.force_login(self.admin)
        response = self.client.get('/admin/moderation-sla/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page'].object_list[0]['kind'], 'place')
        self.assertEqual(response.context['page'].object_list[0]['sla'].status, 'breached')
        limited = get_user_model().objects.create_user('limited', is_staff=True)
        limited.user_permissions.add(Permission.objects.get(codename='change_placereview'))
        self.client.force_login(limited)
        response = self.client.get('/admin/moderation-sla/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['kind'] for row in response.context['page'].object_list}, {'place_review'})
        limited.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        self.assertEqual(self.client.get('/admin/moderation-sla/').status_code, 403)

    def test_queue_filters_and_needs_changes_requires_reason(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin/moderation-sla/?sla_status=breached')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page'].object_list), 0)
        url = f'/admin/moderation-sla/place/{self.place.pk}/needs-changes/'
        self.assertEqual(self.client.post(url, {'reason': ''}).status_code, 400)
        self.assertEqual(self.client.post(url, {'reason': 'Clarify address'}).status_code, 302)
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'needs_changes')
        self.assertEqual(self.place.rejection_reason, 'Clarify address')
        self.assertEqual(self.place.moderated_by_id, self.admin.pk)
        response = self.client.get('/admin/moderation-sla/?status=needs_changes')
        self.assertEqual(response.context['page'].object_list[0]['sla'].status, 'paused')

    def test_site_submission_returns_localized_deadline_and_resets_old_decision(self):
        from django.test import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.utils.translation import override
        from catalog.services.review_use_cases import submit_site_review
        from catalog.models import SiteReview
        request = RequestFactory().post('/', {'rating': '5', 'text': 'Useful catalogue', 'author_name': 'SLA user'})
        request.user = self.admin
        SessionMiddleware(lambda r: None).process_request(request)
        with override('en'):
            result = submit_site_review(request=request, require_auth=True)
        self.assertTrue(result.ok, result.message)
        self.assertIn('24 calendar hours', result.message)
        review = SiteReview.objects.get(user=self.admin)
        review.status = 'approved'
        review.moderated_by = self.admin
        review.save()
        with override('en'):
            result = submit_site_review(request=request, require_auth=True)
        review.refresh_from_db()
        self.assertEqual(review.status, 'pending')
        self.assertIsNone(review.moderated_at)
        self.assertIsNone(review.moderated_by_id)

    def test_specialist_review_admin_decision_tracks_actor(self):
        from django.contrib import admin
        from django.test import RequestFactory
        from catalog.models import Specialist, SpecialistReview
        specialist = Specialist.objects.create(name='SLA Specialist')
        review = SpecialistReview.objects.create(specialist=specialist, user=self.admin, author_name='Reader', text='Good professional')
        self.assertIsNotNone(review.submitted_at)
        request = RequestFactory().post('/')
        request.user = self.admin
        review.status = 'approved'
        admin.site._registry[SpecialistReview].save_model(request, review, None, True)
        review.refresh_from_db()
        self.assertIsNotNone(review.moderated_at)
        self.assertEqual(review.moderated_by_id, self.admin.pk)

    def test_needs_changes_remains_owner_editable(self):
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        self.place.status = 'needs_changes'
        self.assertTrue(OwnerPlacesController._is_user_editable_place(self.place))

    def test_admin_place_bulk_decision_tracks_actor(self):
        from catalog.testcases.utils import create_ready_place
        from django.test import RequestFactory
        from django.contrib import admin
        from django.contrib.messages.storage.fallback import FallbackStorage
        from catalog.models import Place
        place = create_ready_place(status='pending', is_active=False)
        request = RequestFactory().post('/')
        request.user = self.admin
        request.session = {}
        request._messages = FallbackStorage(request)
        admin.site._registry[Place].mark_published(request, Place.objects.filter(pk=place.pk))
        place.refresh_from_db()
        self.assertEqual(place.status, 'published')
        self.assertEqual(place.moderated_by_id, self.admin.pk)

    def test_queue_does_not_count_approved_revision_twice(self):
        from catalog.models import VolunteerPlaceRevision
        from catalog.services.moderation_queue import queue_rows
        self.place.status = 'published'
        self.place.save()
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.admin, status='approved')
        rows = queue_rows(self.admin, {'status': 'approved'}, now=timezone.now())
        self.assertEqual([(row['kind'], row['id']) for row in rows], [('place', self.place.pk)])
