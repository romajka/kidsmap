from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from catalog.models import OfferingGroup, Organization, OrganizationPlaceRequest, PlaceReview, Program, VolunteerPlaceRevision
from catalog.services.moderation_queue import queue_rows
from catalog.services.review_versions import moderate_candidate, review_types, submit_review
from catalog.testcases.test_task33_review_independent import ReviewFixtures
from catalog.testcases.utils import create_quality_place


class ModerationSlaSourcesTests(ReviewFixtures, TestCase):
    def rows(self, user=None, **filters):
        return queue_rows(user or self.staff, filters, now=timezone.now())

    def test_edit_of_approved_review_uses_only_current_candidate_and_links_to_its_workflow(self):
        self.client.force_login(self.staff)
        submitted = timezone.now() - timedelta(hours=3)
        expected = {}
        for kind in review_types():
            target = getattr(self, kind)
            head, _ = self.approved(target)
            submit_review(target=target, user=self.author, rating=4, text='Superseded edit')
            head, edit = submit_review(target=target, user=self.author, rating=3, text=f'Pending {kind} edit')
            type(edit).objects.filter(pk=edit.pk).update(submitted_at=submitted)
            expected[(kind + '_review', head.pk)] = edit
        rows = self.rows(type='review', status='pending')
        self.assertEqual(len(rows), len(expected))
        self.assertSetEqual({(row['kind'], row['id']) for row in rows}, set(expected))
        for row in rows:
            edit = expected[row['kind'], row['id']]
            self.assertEqual(row['name'], edit.text)
            self.assertEqual(row['submitted_at'], submitted)
            self.assertEqual(row['sla'].deadline, submitted + timedelta(hours=24))
            workflow = self.client.get(row['url'])
            self.assertEqual(workflow.status_code, 200)
            self.assertEqual(workflow.context['candidate'].pk, edit.pk)

    def test_rejected_edit_reports_its_decision_while_older_text_stays_public(self):
        head, approved = self.approved()
        _, edit = submit_review(target=self.place, user=self.author, rating=2, text='Later rejected submission')
        moderate_candidate(head=head, revision_id=edit.pk, actor=self.staff, approve=False, reason='Correction needed')
        edit.refresh_from_db()
        head.refresh_from_db()
        self.assertEqual(head.current_revision_id, approved.pk)
        self.assertEqual(head.status, 'approved')
        rows = self.rows(type='place_review', status='rejected')
        self.assertEqual([(row['id'], row['name']) for row in rows], [(head.pk, edit.text)])
        self.assertEqual(rows[0]['sla'].status, 'completed')
        self.assertEqual(rows[0]['submitted_at'], edit.submitted_at)
        self.assertEqual(len(self.rows(type='place_review', status='all')), 1)
        self.assertEqual(self.rows(type='place_review', status='approved'), [])

    def test_http_review_submissions_and_type_permissions(self):
        self.client.force_login(self.author)
        for kind in ('event', 'activity'):
            response = self.client.post(reverse('typed_reviews', args=[kind, getattr(self, kind).pk]),
                                        {'rating': '5', 'text': f'My {kind} review'})
            self.assertEqual(response.status_code, 302)
        limited = get_user_model().objects.create_user('activity-reviewer', is_staff=True)
        limited.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_activityreview'))
        rows = self.rows(limited, type='review')
        self.assertEqual([row['kind'] for row in rows], ['activity_review'])
        self.client.force_login(limited)
        self.assertEqual(self.client.get(rows[0]['url']).status_code, 200)
        event_row, = self.rows(type='event_review')
        self.assertEqual(self.client.get(event_row['url']).status_code, 403)

    def test_legacy_head_without_history_is_counted_once_and_archived_head_is_excluded(self):
        live, _ = PlaceReview.objects.bulk_create([
            PlaceReview(place=self.place, status='pending', text='Imported current', is_current=True),
            PlaceReview(place=self.place, status='pending', text='Historical source', is_current=False),
        ])
        rows = self.rows(type='place_review')
        self.assertEqual([(row['id'], row['name']) for row in rows], [(live.pk, live.text)])
        self.assertTrue(rows[0]['estimated'])
        self.assertFalse(live.revisions.exists())

    def test_single_import_baseline_keeps_later_correction_of_legacy_submission_date(self):
        head = PlaceReview.objects.create(place=self.place, status='pending', text='Imported with history')
        baseline = head.revisions.get()
        self.assertTrue(baseline.is_baseline)
        corrected = baseline.created_at - timedelta(days=2)
        PlaceReview.objects.filter(pk=head.pk).update(submitted_at=corrected)
        row, = self.rows(type='place_review')
        self.assertEqual(row['submitted_at'], corrected)
        self.assertEqual(row['sla'].deadline, corrected + timedelta(hours=24))

    def test_final_place_refusal_is_completed_once_and_uses_revision_dates(self):
        submitted = timezone.now() - timedelta(hours=5)
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.author,
            status='declined', payload={'name_az': 'Refused edition'}, submitted_at=submitted,
            moderated_at=submitted + timedelta(hours=2))
        rows = self.rows(type='place', status='rejected')
        self.assertEqual([(row['kind'], row['id']) for row in rows], [('place_revision', revision.pk)])
        self.assertEqual(rows[0]['submitted_at'], submitted)
        self.assertEqual(rows[0]['age_hours'], 2)
        self.assertEqual(rows[0]['sla'].status, 'completed')
        self.assertEqual(len(self.rows(type='place', status='all')), 1)

    def test_approved_place_keeps_one_row_with_the_submission_and_decision_of_its_edit(self):
        submitted = timezone.now() - timedelta(hours=7)
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.author, status='approved',
            submitted_at=submitted, moderated_at=submitted + timedelta(hours=3))
        row, = self.rows(type='place', status='approved')
        self.assertEqual((row['kind'], row['id']), ('place', self.place.pk))
        self.assertEqual(row['submitted_at'], submitted)
        self.assertEqual(row['age_hours'], 3)

    def test_all_statuses_cannot_reintroduce_a_stale_pending_place_as_actionable(self):
        place = create_quality_place(status='pending')
        VolunteerPlaceRevision.objects.create(place=place, author=self.author, status='approved')
        self.assertEqual(self.rows(type='place', status='pending'), [])
        false_pending = [row for row in self.rows(type='place', status='all') if row['status'] == 'pending']
        self.assertEqual(false_pending, [])
        approved_ids = [row['id'] for row in self.rows(type='place', status='approved')]
        self.assertIn(place.pk, approved_ids)

    def test_proposal_type_includes_entity_proposals_only(self):
        org = Organization.objects.create(name_az='Organization')
        program = Program.objects.create(organization=org, name_az='Program')
        group = OfferingGroup.objects.create(activity=self.activity, name_az='Group')
        expected = set()
        for kind, target in [('organization', org), ('program', program), ('activity', self.activity), ('offering_group', group)]:
            revision = VolunteerPlaceRevision.objects.create(**{kind: target}, author=self.author,
                status='pending', payload={'name_az': 'Submitted ' + kind})
            expected.add((kind + '_revision', revision.pk, 'Submitted ' + kind))
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.author, status='pending')
        link = OrganizationPlaceRequest.objects.create(place=self.place, organization=org, relationship_kind='informational')
        self.assertSetEqual({(row['kind'], row['id'], row['name']) for row in self.rows(type='proposals')}, expected)
        self.assertEqual(self.rows(self.author, type='proposals'), [])
        link_reviewer = get_user_model().objects.create_user('link-reviewer', is_staff=True)
        link_reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_placeownershiprequest'))
        self.assertEqual([(row['kind'], row['id']) for row in self.rows(link_reviewer)], [('affiliation', link.pk)])
        self.assertEqual(self.rows(link_reviewer, type='proposals'), [])

    def test_default_queue_queries_do_not_grow_with_unsubmitted_place_drafts(self):
        self.rows()  # Warm the staff permission/group caches.
        with CaptureQueriesContext(connection) as before:
            initial_rows = self.rows()
        for _ in range(4):
            VolunteerPlaceRevision.objects.create(place=create_quality_place(), author=self.author, status='draft')
        with CaptureQueriesContext(connection) as after:
            self.assertEqual(self.rows(), initial_rows)
        self.assertEqual(len(after), len(before))

    def test_revoking_cached_staff_permission_hides_proposal_on_the_next_queue_read(self):
        org = Organization.objects.create(name_az='Restricted proposal')
        VolunteerPlaceRevision.objects.create(organization=org, author=self.author, status='pending')
        reviewer = get_user_model().objects.create_user('proposal-reviewer', is_staff=True)
        grant = Permission.objects.get(content_type__app_label='catalog', codename='change_place')
        reviewer.user_permissions.add(grant)
        self.assertTrue(reviewer.has_perm('catalog.change_place'))
        self.assertEqual(len(self.rows(reviewer, type='proposals')), 1)
        reviewer.user_permissions.remove(grant)
        self.assertEqual(self.rows(reviewer, type='proposals'), [])

    def test_legacy_returned_proposal_with_missing_pause_timestamp_stays_paused(self):
        submitted = timezone.now() - timedelta(hours=8)
        org = Organization.objects.create(name_az='Returned proposal')
        revision = VolunteerPlaceRevision.objects.create(organization=org, author=self.author, status='rejected')
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(
            submitted_at=submitted, needs_changes_at=None, moderated_at=None, updated_at=submitted + timedelta(hours=2))
        row, = self.rows(type='proposals', status='needs_changes')
        self.assertEqual(row['sla'].status, 'paused')
        self.assertEqual(row['age_hours'], 2)
