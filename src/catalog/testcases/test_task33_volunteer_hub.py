"""Stage 16 trust-boundary and moderation integration tests."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import TestCase
from catalog.models import Activity, Organization, OrganizationPlaceRequest, Place, Program, VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place


class VolunteerHubTests(TestCase):
    def setUp(self):
        user = get_user_model()
        group, _ = Group.objects.get_or_create(name='KidsMap Volunteers')
        self.a = user.objects.create_user('vol_a', is_staff=True)
        self.b = user.objects.create_user('vol_b', is_staff=True)
        self.a.groups.add(group)
        self.b.groups.add(group)
        self.reviewer = user.objects.create_superuser('vol_reviewer', 'reviewer@example.invalid', 'synthetic')
        self.place = create_quality_place(created_by=self.a, owner=None, with_subcategory=True, with_pricing_plan=True, with_schedule_days=True)
        self.org = Organization.objects.create(created_by=self.a, owner=None, name_az='Mərkəz')
        self.program = Program.objects.create(organization=self.org, created_by=self.a, name_az='Kurs')
        self.activity = Activity.objects.create(place=self.place, name_az='Məşğələ')

    def test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id(self):
        from catalog.services import volunteer_proposals
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version, revision_version=0, submit=False)
        with self.assertRaises(Http404):
            volunteer_proposals.get_candidate(actor=self.b, revision_id=revision.pk)
        with self.assertRaises(PermissionDenied):
            volunteer_proposals.propose(actor=self.b, kind='organization', target_id=self.org.pk,
                patch={'description_az': 'Hijack'}, expected_version=self.org.content_version, revision_version=revision.version, submit=True)
        self.assertEqual(VolunteerPlaceRevision.objects.get(pk=revision.pk).payload['description_az'], 'Candidate')

    def test_volunteer_org_and_program_publish_without_business_grant(self):
        from catalog.services import volunteer_proposals, publication
        for kind, target in [('organization', self.org), ('program', self.program)]:
            revision = volunteer_proposals.propose(actor=self.a, kind=kind, target_id=target.pk,
                patch={'description_az': f'{kind} candidate'}, expected_version=target.content_version,
                revision_version=0, submit=True)
            publication.review(actor=self.reviewer, revision_id=revision.pk, version=revision.version, approve=True)
            target.refresh_from_db()
            self.assertEqual(target.status, 'published')
            self.assertIsNone(self.org.owner_id)
            self.assertEqual(target.description_az, f'{kind} candidate')

    def test_owner_handover_schema_and_stale_source_block_approval(self):
        from catalog.services import volunteer_proposals, publication
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        Organization.objects.filter(pk=self.org.pk).update(owner=self.b, ownership_version=2)
        with self.assertRaises((PermissionDenied, ValidationError)):
            publication.review(actor=self.reviewer, revision_id=revision.pk, version=revision.version, approve=True)
        self.org.refresh_from_db()
        self.assertNotEqual(self.org.description_az, 'Candidate')
        with self.assertRaises((PermissionDenied, ValidationError)):
            volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
                patch={'description_az': 'Bad schema'}, expected_version=self.org.content_version,
                revision_version=revision.version, submit=True, schema_version=999)

    def test_return_keeps_candidate_and_final_reject_records_reason(self):
        from catalog.services import volunteer_proposals
        revision = volunteer_proposals.propose(actor=self.a, kind='activity', target_id=self.activity.pk,
            patch={'description_az': 'Volunteer text'}, expected_version=self.activity.content_version,
            revision_version=0, submit=True)
        returned = volunteer_proposals.review(actor=self.reviewer, revision_id=revision.pk,
            version=revision.version, action='return', reason='More details')
        self.assertEqual(returned.status, 'rejected')
        self.assertEqual(returned.payload['description_az'], 'Volunteer text')
        self.assertEqual(returned.review_note, 'More details')
        resubmitted = volunteer_proposals.propose(actor=self.a, kind='activity', target_id=self.activity.pk,
            patch={'description_az': 'Better text'}, expected_version=self.activity.content_version,
            revision_version=returned.version, submit=True)
        declined = volunteer_proposals.review(actor=self.reviewer, revision_id=revision.pk,
            version=resubmitted.version, action='reject', reason='Unsupported')
        self.assertEqual(declined.status, 'declined')
        self.assertEqual(declined.review_note, 'Unsupported')
        self.assertIsNotNone(declined.moderated_at)

    def test_informational_approval_without_business_grant(self):
        from catalog.services import volunteer_proposals
        request = volunteer_proposals.submit_informational_link(actor=self.a, place_id=self.place.pk,
            organization_id=self.org.pk)
        self.assertEqual(request.status, 'pending')
        volunteer_proposals.review_informational_link(actor=self.reviewer, request_id=request.pk,
            action='approve', reason='Checked', expected_place_version=self.place.content_version)
        self.place.refresh_from_db()
        self.assertEqual(self.place.organization_id, self.org.pk)
        self.assertEqual(self.place.organization_relationship_kind, 'informational')
        self.assertIsNone(self.place.owner_id)
        self.assertIsNone(self.org.owner_id)
        self.assertFalse(self.place.team_memberships.exists())

    def test_hub_filters_and_counts_include_all_content_and_links(self):
        from catalog.services import volunteer_proposals, moderation_hub
        for kind, target in [('organization', self.org), ('program', self.program), ('activity', self.activity)]:
            volunteer_proposals.propose(actor=self.a, kind=kind, target_id=target.pk,
                patch={'description_az': 'Candidate'}, expected_version=target.content_version,
                revision_version=0, submit=True)
        link = volunteer_proposals.submit_informational_link(actor=self.a, place_id=self.place.pk,
            organization_id=self.org.pk)
        rows, counts = moderation_hub.query(self.reviewer, {'status': 'pending'})
        self.assertEqual(counts['pending'], 4)
        self.assertEqual({row['kind'] for row in rows}, {'organization', 'program', 'activity', 'affiliation'})
        filtered, _ = moderation_hub.query(self.reviewer, {'entity': 'affiliation', 'author': str(self.a.pk)})
        self.assertEqual([row['id'] for row in filtered], [link.pk])
        self.assertEqual(moderation_hub.query(self.reviewer, {'entity': 'program', 'place': str(self.place.pk)})[0], [])

    def test_creation_keeps_program_and_activity_private_until_review(self):
        from catalog.services import volunteer_proposals
        program = volunteer_proposals.create_and_propose(actor=self.a, kind='program', parent_id=self.org.pk,
            patch={'name_az': 'Yeni kurs'}, submit=True)
        activity = volunteer_proposals.create_and_propose(actor=self.a, kind='activity', parent_id=self.place.pk,
            patch={'name_az': 'Yeni məşğələ'}, submit=True)
        self.assertEqual(program.status, 'pending')
        self.assertEqual(activity.status, 'pending')
        self.assertEqual(program.program.organization_id, self.org.pk)
        self.assertEqual(activity.activity.place_id, self.place.pk)
        self.assertEqual(program.program.status, 'draft')
        self.assertEqual(activity.activity.status, 'draft')
        self.assertIsNone(self.org.owner_id)

    def test_direct_http_object_substitution_denies_foreign_drafts(self):
        from django.urls import reverse
        self.client.force_login(self.b)
        url = reverse('admin:volunteer_proposal_edit', args=['organization', self.org.pk])
        self.assertIn(self.client.get(url).status_code, (403, 404))
        self.assertIn(self.client.post(url, {'action': 'submit', 'description_az': 'Hijack',
            'expected_version': self.org.content_version, 'revision_version': 0}).status_code, (403, 404))
        self.client.force_login(self.a)
        from catalog.services import volunteer_proposals
        self.assertEqual(volunteer_proposals.get_target(actor=self.a, kind='organization', target_id=self.org.pk)[0].pk, self.org.pk)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_informational_link_stale_place_version_blocks_approval(self):
        from catalog.services import volunteer_proposals
        request = volunteer_proposals.submit_informational_link(actor=self.a, place_id=self.place.pk,
            organization_id=self.org.pk)
        Place.objects.filter(pk=self.place.pk).update(content_version=self.place.content_version + 1)
        with self.assertRaises(ValidationError):
            volunteer_proposals.review_informational_link(actor=self.reviewer, request_id=request.pk,
                action='approve', reason='Checked', expected_place_version=self.place.content_version)
        request.refresh_from_db()
        self.assertEqual(request.status, 'pending')

    def test_hub_get_post_ajax_and_version_conflict(self):
        from django.urls import reverse
        from catalog.services import volunteer_proposals
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        index = reverse('admin:volunteer_moderation_hub')
        detail = reverse('admin:volunteer_moderation_detail', args=['content', revision.pk])
        self.client.force_login(self.a)
        self.assertEqual(self.client.get(index).status_code, 403)
        self.assertEqual(self.client.get(detail).status_code, 403)
        self.assertEqual(self.client.post(detail, {'action': 'approve', 'version': revision.version,
            'reason': 'No'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 403)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(index, {'entity': 'organization', 'status': 'pending'}).status_code, 200)
        self.assertContains(self.client.get(detail), 'Candidate')
        stale = self.client.post(detail, {'action': 'approve', 'version': revision.version - 1,
            'reason': 'Checked'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(stale.status_code, 409)
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        approved = self.client.post(detail, {'action': 'approve', 'version': revision.version,
            'reason': 'Checked'})
        self.assertEqual(approved.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.description_az, 'Candidate')

    def test_hub_program_preview_lists_affected_branches(self):
        from django.urls import reverse
        from catalog.services import volunteer_proposals
        Place.objects.filter(pk=self.place.pk).update(organization=self.org)
        self.place.refresh_from_db()
        linked = Activity.objects.create(place=self.place, program=self.program, name_az='Local')
        revision = volunteer_proposals.propose(actor=self.a, kind='program', target_id=self.program.pk,
            patch={'description_az': 'New common text'}, expected_version=self.program.content_version,
            revision_version=0, submit=True)
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse('admin:volunteer_moderation_detail', args=['content', revision.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.place.pk))
        self.assertEqual(response.context['row']['affected_branches'], [self.place.pk])
        self.assertEqual(linked.program_id, self.program.pk)

    def test_affiliation_form_rejects_foreign_private_target(self):
        from django.urls import reverse
        other_org = Organization.objects.create(created_by=self.b, owner=None, name_az='Private')
        self.client.force_login(self.a)
        url = reverse('admin:volunteer_affiliation_add')
        response = self.client.post(url, {'place_id': self.place.pk, 'organization_id': other_org.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(OrganizationPlaceRequest.objects.filter(place=self.place, organization=other_org).exists())

    def test_my_proposals_list_is_author_scoped_and_does_not_expose_staff_links(self):
        from catalog.services import volunteer_proposals
        from django.urls import reverse
        own = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Own private draft'}, expected_version=self.org.content_version,
            revision_version=0, submit=False)
        foreign = volunteer_proposals.create_and_propose(actor=self.b, kind='organization',
            patch={'name_az': 'Other private draft'}, submit=False)
        self.client.force_login(self.a)
        response = self.client.get(reverse('admin:volunteer_index'))
        self.assertContains(response, 'Own private draft')
        self.assertNotContains(response, 'Other private draft')
        self.assertNotContains(response, '/admin/catalog/organization/')
        self.assertNotContains(response, '/admin/auth/user/')
        self.assertEqual(own.author_id, self.a.pk)
        self.assertEqual(foreign.author_id, self.b.pk)

    def test_schema_conflict_and_stale_field_do_not_apply_candidate(self):
        from catalog.services import volunteer_proposals, publication
        with self.assertRaises(ValidationError):
            volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
                patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
                revision_version=0, submit=True, schema_version=99)
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        Organization.objects.filter(pk=self.org.pk).update(description_az='Fresh')
        with self.assertRaises(ValidationError):
            publication.review(actor=self.reviewer, revision_id=revision.pk,
                version=revision.version, approve=True)
        self.org.refresh_from_db()
        self.assertEqual(self.org.description_az, 'Fresh')

    def test_same_public_affiliation_pending_remains_author_scoped(self):
        from catalog.services import volunteer_proposals
        Organization.objects.filter(pk=self.org.pk).update(status='published')
        Place.objects.filter(pk=self.place.pk).update(status='published', is_active=True)
        request = volunteer_proposals.submit_informational_link(actor=self.a, place_id=self.place.pk,
            organization_id=self.org.pk)
        with self.assertRaises(PermissionDenied):
            volunteer_proposals.submit_informational_link(actor=self.b, place_id=self.place.pk,
                organization_id=self.org.pk)
        self.assertEqual(OrganizationPlaceRequest.objects.filter(place=self.place, organization=self.org, status='pending').count(), 1)
        self.assertEqual(request.requested_by_id, self.a.pk)

    def test_existing_sla_queue_counts_new_proposal_types(self):
        from django.utils import timezone
        from catalog.services import volunteer_proposals
        from catalog.services.moderation_queue import queue_rows
        volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        rows = queue_rows(self.reviewer, {'status': 'pending'}, now=timezone.now())
        self.assertIn('organization_revision', {row['kind'] for row in rows})
        self.assertTrue(all(row['sla'].deadline for row in rows if row['kind'] == 'organization_revision'))

    def test_missing_hub_item_is_not_a_server_error(self):
        from django.urls import reverse
        self.client.force_login(self.reviewer)
        response = self.client.get(reverse('admin:volunteer_moderation_detail', args=['content', 999999]))
        self.assertEqual(response.status_code, 404)

    def test_empty_new_organization_draft_needs_no_invented_name(self):
        from catalog.services import volunteer_proposals
        revision = volunteer_proposals.create_and_propose(actor=self.a, kind='organization', patch={}, submit=False)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.organization.name_az, '')
        self.assertIsNone(revision.organization.owner_id)
        with self.assertRaises(ValidationError):
            volunteer_proposals.create_and_propose(actor=self.a, kind='organization', patch={}, submit=True)

    def test_hub_respects_distinct_content_and_affiliation_reviewer_permissions(self):
        from django.contrib.auth.models import Permission
        from django.urls import reverse
        from catalog.services import volunteer_proposals
        content = get_user_model().objects.create_user('content_reviewer', is_staff=True)
        content.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_place'))
        links = get_user_model().objects.create_user('link_reviewer', is_staff=True)
        links.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_placeownershiprequest'))
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        request = volunteer_proposals.submit_informational_link(actor=self.a, place_id=self.place.pk,
            organization_id=self.org.pk)
        own_links = [row for row in volunteer_proposals.own_proposal_rows(self.a) if row['kind'] == 'affiliation']
        self.assertEqual(len(own_links), 1)
        self.assertIn('Mərkəz', own_links[0]['name'])
        content_url = reverse('admin:volunteer_moderation_detail', args=['content', revision.pk])
        link_url = reverse('admin:volunteer_moderation_detail', args=['affiliation', request.pk])
        self.client.force_login(content)
        self.assertEqual(self.client.get(content_url).status_code, 200)
        self.assertEqual(self.client.get(link_url).status_code, 404)
        self.client.force_login(links)
        self.assertEqual(self.client.get(content_url).status_code, 404)
        self.assertEqual(self.client.get(link_url).status_code, 200)
        from django.utils.translation import override
        with override('ru'):
            sla_response = self.client.get(reverse('admin:moderation_sla') + '?type=affiliation')
            self.assertEqual(sla_response.status_code, 200)
            self.assertEqual([row['kind'] for row in sla_response.context['page'].object_list], ['affiliation'])
            self.assertIn('Mərkəz', sla_response.context['page'].object_list[0]['name'])
            self.assertIn('type_filters', sla_response.context)
            self.assertIn(('affiliation', 'Информационная связь'), sla_response.context['type_filters'])
            self.assertEqual(sla_response.context['links_count'], 1)
            sidebar = next(section for section in sla_response.context['kidsmap_sidebar_sections'] if section['key'] == 'moderation_sla')
            self.assertEqual(sidebar['items'][0]['label'], 'Сроки модерации')
        from django.utils import timezone
        from catalog.services.moderation_queue import queue_rows
        link_rows = queue_rows(links, {'status': 'pending'}, now=timezone.now())
        self.assertIn(request.pk, [row['id'] for row in link_rows if row['kind'] == 'affiliation'])
        self.assertNotIn(revision.pk, [row['id'] for row in link_rows if row['kind'] == 'organization_revision'])
        response = self.client.post(link_url, {'action': 'approve', 'version': self.place.content_version,
            'reason': 'Checked'})
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertEqual(self.place.organization_relationship_kind, 'informational')

    def test_revoked_volunteer_candidate_remains_visible_for_reviewer_resolution(self):
        from catalog.services import volunteer_proposals, moderation_hub
        revision = volunteer_proposals.propose(actor=self.a, kind='organization', target_id=self.org.pk,
            patch={'description_az': 'Candidate'}, expected_version=self.org.content_version,
            revision_version=0, submit=True)
        self.a.groups.clear()
        self.a.is_active = False
        self.a.save(update_fields=['is_active'])
        rows, counts = moderation_hub.query(self.reviewer, {'status': 'pending'})
        self.assertIn(revision.pk, [row['id'] for row in rows if row['kind'] == 'organization'])
        self.assertEqual(counts['pending'], 1)
        self.assertTrue(moderation_hub.detail(self.reviewer, 'content', revision.pk))
