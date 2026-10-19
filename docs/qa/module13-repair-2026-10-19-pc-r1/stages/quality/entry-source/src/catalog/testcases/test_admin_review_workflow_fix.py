"""Admin decisions bind the displayed candidate and keep visible history separate."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Place, PlaceReview
from catalog.proxy_apps.catalog_moderation.models import ModerationReview
from catalog.services.review_versions import submit_review, moderate_candidate, rating_summary
from catalog.testcases.utils import create_quality_place


class AdminReviewWorkflowFixTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_superuser('fix-reviewer', 'reviewer@example.invalid', 'synthetic-only')
        self.author = User.objects.create_user('fix-author')
        self.place = create_quality_place()
        self.client.force_login(self.staff)

    def pending(self, text='Candidate review text', rating=4):
        return submit_review(target=self.place, user=self.author, rating=rating, text=text, author_name='Review author')

    def approved(self):
        head, revision = self.pending('Published original text', 2)
        moderate_candidate(head=head, revision_id=revision.pk, actor=self.staff, approve=True)
        head.refresh_from_db()
        return head, revision

    def action(self, head, action):
        return reverse('admin:catalog_placereview_' + action, args=[head.pk])

    def workflow(self, head):
        return reverse('admin:catalog_placereview_workflow', args=[head.pk])

    def bulk(self, action, heads, *, snapshot=None, proxy=True):
        url = reverse('admin:catalog_moderation_moderationreview_changelist' if proxy else 'admin:catalog_placereview_changelist')
        if snapshot is None:
            response = self.client.get(url)
            snapshot = response.context_data.get('review_snapshot', '')
        return self.client.post(url, {'action': action, '_selected_action': [h.pk for h in heads], 'review_snapshot': snapshot})

    @override_settings(ADMIN_HOST='admin.audit.invalid', PUBLIC_BASE_URL='https://public.audit.invalid')
    def test_workflow_stays_on_admin_origin_and_guest_never_sees_candidate(self):
        head, candidate = self.pending()
        response = self.client.get(self.workflow(head), HTTP_HOST='admin.audit.invalid', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, candidate.text)
        self.assertContains(response, self.action(head, 'approve'))
        self.assertNotContains(response, reverse('typed_review_action', args=['place', head.pk, 'approve']))
        self.client.logout()
        public = self.client.get(reverse('typed_reviews', args=['place', self.place.pk]), HTTP_HOST='public.audit.invalid', secure=True)
        self.assertNotContains(public, candidate.text)
        denied = self.client.get(self.workflow(head), HTTP_HOST='admin.audit.invalid', secure=True)
        self.assertEqual(denied.status_code, 302)

    def test_workflow_allows_permissioned_hidden_target_without_publicizing_it(self):
        Place.objects.filter(pk=self.place.pk).update(status='pending')
        head, candidate = self.pending()
        self.assertContains(self.client.get(self.workflow(head)), candidate.text)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('typed_reviews', args=['place', self.place.pk])).status_code, 404)

    def test_staff_without_concrete_permission_cannot_read_or_act(self):
        head, candidate = self.pending()
        staff = get_user_model().objects.create_user('no-review-permission', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.workflow(head)).status_code, 403)
        self.assertEqual(self.client.post(self.action(head, 'approve'), {'revision_id': candidate.pk}).status_code, 403)
        head.refresh_from_db()
        self.assertIsNone(head.current_revision_id)

    def test_proxy_accepts_concrete_permission_and_queues_published_edit(self):
        head, old = self.approved()
        head, candidate = self.pending('Replacement awaiting moderation', 5)
        staff = get_user_model().objects.create_user('concrete-review-permission', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_placereview'))
        self.client.force_login(staff)
        url = reverse('admin:catalog_moderation_moderationreview_changelist')
        response = self.client.get(url)
        self.assertContains(response, candidate.text)
        self.assertEqual(list(response.context_data['cl'].queryset.values_list('pk', flat=True)), [head.pk])
        result = self.bulk('approve_selected', [head])
        self.assertEqual(result.status_code, 302)
        head.refresh_from_db()
        self.assertEqual((head.current_revision_id, head.candidate_revision_id), (candidate.pk, None))

    def test_dashboard_count_and_preview_include_pending_published_edit(self):
        head, old = self.approved()
        head, candidate = self.pending('Dashboard candidate text', 5)
        from catalog.templatetags.admin_dashboard_tags import get_dashboard_stats
        stats = get_dashboard_stats()
        self.assertEqual(stats['pending']['reviews'], 1)
        self.assertEqual(stats['pending_reviews'][0]['text'], candidate.text)
        self.assertEqual(stats['pending_reviews'][0]['rating'], candidate.rating)

    def test_single_approval_is_atomic_and_repeat_is_conflict(self):
        head, candidate = self.pending()
        url = self.action(head, 'approve')
        self.assertEqual(self.client.post(url, {'revision_id': candidate.pk}).status_code, 302)
        head.refresh_from_db(); candidate.refresh_from_db()
        self.assertEqual((head.current_revision_id, head.candidate_revision_id, candidate.status), (candidate.pk, None, 'approved'))
        self.assertEqual(candidate.moderated_by_id, self.staff.pk)
        self.assertEqual(self.client.post(url, {'revision_id': candidate.pk}).status_code, 409)

    def test_legacy_action_get_confirms_exact_candidate_missing_or_replaced_token_fails(self):
        head, candidate = self.pending()
        url = self.action(head, 'approve')
        self.assertContains(self.client.get(url), f'name="revision_id" value="{candidate.pk}"')
        self.assertEqual(self.client.post(url).status_code, 400)
        head, newer = self.pending('Newer candidate text')
        self.assertEqual(self.client.post(url, {'revision_id': candidate.pk}).status_code, 409)
        head.refresh_from_db()
        self.assertEqual(head.candidate_revision_id, newer.pk)
        self.assertIsNone(head.current_revision_id)

    def test_bulk_approval_finishes_candidate_and_updates_public_rating(self):
        head, candidate = self.pending(rating=5)
        self.assertEqual(self.bulk('approve_selected', [head]).status_code, 302)
        head.refresh_from_db(); candidate.refresh_from_db()
        self.assertEqual((head.current_revision_id, head.candidate_revision_id, candidate.status), (candidate.pk, None, 'approved'))
        self.assertEqual(rating_summary(self.place), {'average': 5., 'count': 1})

    def test_bulk_reject_preserves_published_text_and_reason(self):
        head, old = self.approved()
        head, candidate = self.pending('Rejected candidate text', 5)
        self.assertEqual(self.bulk('reject_selected', [head]).status_code, 302)
        head.refresh_from_db(); candidate.refresh_from_db()
        self.assertEqual((head.current_revision_id, head.candidate_revision_id, head.text), (old.pk, None, old.text))
        self.assertEqual(candidate.status, 'rejected')
        self.assertTrue(head.is_approved)
        self.assertEqual(rating_summary(self.place)['average'], 2.)

    def test_bulk_snapshot_refuses_replacement_or_repeat_and_no_partial_decisions(self):
        first, first_candidate = self.pending()
        second_author = get_user_model().objects.create_user('second-queued-author')
        head, candidate = submit_review(target=self.place, user=second_author, rating=3, text='Second queued review')
        url = reverse('admin:catalog_moderation_moderationreview_changelist')
        snapshot = self.client.get(url).context_data.get('review_snapshot', '')
        head, newer = submit_review(target=self.place, user=second_author, rating=4, text='Replaced after list render')
        response = self.bulk('approve_selected', [first, head], snapshot=snapshot)
        self.assertEqual(response.status_code, 409)
        first.refresh_from_db(); first_candidate.refresh_from_db()
        self.assertIsNone(first.current_revision_id)
        self.assertEqual(first.candidate_revision_id, first_candidate.pk)
        self.assertEqual(first_candidate.status, 'pending')
        head.refresh_from_db()
        self.assertIsNone(head.current_revision_id)
        self.assertEqual(head.candidate_revision_id, newer.pk)

    def test_hide_preserves_pending_candidate_history_and_restore_keeps_it_pending(self):
        head, old = self.approved()
        head, candidate = self.pending('Private pending text', 5)
        original_history = list(head.revisions.values_list('pk', 'status', 'text'))
        params = {'expected_current_revision_id': old.pk, 'expected_visibility': '1'}
        self.assertEqual(self.client.post(self.action(head, 'hide'), params).status_code, 302)
        head.refresh_from_db()
        self.assertFalse(head.is_approved)
        self.assertEqual((head.current_revision_id, head.candidate_revision_id), (old.pk, candidate.pk))
        self.assertEqual(list(head.revisions.values_list('pk', 'status', 'text')), original_history)
        self.assertEqual(rating_summary(self.place)['count'], 0)
        self.assertEqual(self.client.post(self.action(head, 'hide'), params).status_code, 409)
        self.assertEqual(self.client.post(self.action(head, 'restore'), {'expected_current_revision_id': old.pk, 'expected_visibility': '0'}).status_code, 302)
        head.refresh_from_db(); candidate.refresh_from_db()
        self.assertTrue(head.is_approved)
        self.assertEqual(head.candidate_revision_id, candidate.pk)
        self.assertEqual(candidate.status, 'pending')
        self.assertEqual(rating_summary(self.place)['average'], 2.)

    def test_hide_without_candidate_creates_no_pending_candidate(self):
        head, old = self.approved()
        self.assertEqual(self.client.post(self.action(head, 'hide'), {'expected_current_revision_id': old.pk, 'expected_visibility': '1'}).status_code, 302)
        head.refresh_from_db()
        self.assertFalse(head.is_approved)
        self.assertIsNone(head.candidate_revision_id)
        self.assertEqual(head.revisions.count(), 1)

    def test_stale_visibility_cannot_hide_newly_approved_revision(self):
        head, old = self.approved()
        head, candidate = self.pending('Next public version')
        moderate_candidate(head=head, revision_id=candidate.pk, actor=self.staff, approve=True)
        self.assertEqual(self.client.post(self.action(head, 'hide'), {'expected_current_revision_id': old.pk, 'expected_visibility': '1'}).status_code, 409)
        head.refresh_from_db()
        self.assertTrue(head.is_approved)
        self.assertEqual(head.current_revision_id, candidate.pk)

    def test_bulk_without_snapshot_cannot_approve_current_unseen_candidate(self):
        head, candidate = self.pending()
        self.assertEqual(self.bulk('approve_selected', [head], snapshot='').status_code, 400)
        head.refresh_from_db()
        self.assertIsNone(head.current_revision_id)

    def test_place_inline_cannot_mutate_projection_outside_review_workflow(self):
        from catalog.domain_admin.review import PlaceReviewInline
        from django.contrib import admin
        from django.test import RequestFactory
        head, candidate = self.pending()
        request = RequestFactory().get('/')
        request.user = self.staff
        inline = PlaceReviewInline(Place, admin.site)
        self.assertFalse(inline.has_add_permission(request, self.place))
        self.assertFalse(inline.has_delete_permission(request, self.place))
        formset = inline.get_formset(request, self.place)
        self.assertEqual(set(formset.form.base_fields), set())
        self.assertIn(self.workflow(head), str(inline.review_workflow_link(head)))

    def test_all_typed_admins_use_signed_bulk_and_preserve_candidate_when_hidden(self):
        from catalog.models import Activity, Event, Specialist
        from django.utils import timezone
        from datetime import timedelta
        targets = [
            Specialist.objects.create(owner=self.author, name='Workflow specialist', status='published', is_active=True),
            Activity.objects.create(place=self.place, status='published', name_az='Workflow activity'),
            Event.objects.create(owner=self.author, name='Workflow event', category=self.place.category,
                start_datetime=timezone.now()+timedelta(days=1), end_datetime=timezone.now()+timedelta(days=1,hours=1)),
        ]
        for target in targets:
            with self.subTest(kind=target._meta.model_name):
                head, revision = submit_review(target=target, user=self.author, rating=5, text='Typed candidate', author_name='Author')
                prefix = 'admin:catalog_' + head._meta.model_name
                url = reverse(prefix + '_changelist')
                def bulk(action):
                    snapshot = self.client.get(url).context_data['review_snapshot']
                    return self.client.post(url, {'action': action, '_selected_action': [head.pk], 'review_snapshot': snapshot})
                self.assertEqual(bulk('approve_selected').status_code, 302)
                head.refresh_from_db(); revision.refresh_from_db()
                self.assertEqual((head.current_revision_id, head.candidate_revision_id, revision.status), (revision.pk, None, 'approved'))
                head, candidate = submit_review(target=target, user=self.author, rating=1, text='New private edit', author_name='Author')
                self.assertEqual(bulk('hide_selected').status_code, 302)
                head.refresh_from_db(); candidate.refresh_from_db()
                self.assertEqual((head.is_approved, head.candidate_revision_id, candidate.status), (False, candidate.pk, 'pending'))
                self.assertEqual(rating_summary(target)['count'], 0)
