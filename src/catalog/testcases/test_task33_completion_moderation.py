"""Cross-target pending revisions must not break the legacy Place review screen."""
from django.test import TestCase
from django.urls import reverse
from catalog.models import Program, VolunteerPlaceRevision
from catalog.services import publication
from catalog.testcases.test_task33_ownership import OwnershipFixture


class MixedModerationQueueTests(OwnershipFixture, TestCase):
    def test_place_review_index_with_pending_program_and_place(self):
        program = Program.objects.create(organization=self.org, name_az='Mixed queue program')
        program_revision = publication.propose(actor=self.b, target_type='program', target_id=program.pk,
            patch={'description_az': 'Pending program description'}, schema_version=1,
            expected_version=program.content_version, revision_version=0, submit=True)
        place_revision = publication.propose(actor=self.a, target_type='place', target_id=self.place.pk,
            patch={'name_az': 'Pending place name'}, schema_version=1,
            expected_version=self.place.content_version, revision_version=0, submit=True)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:volunteer_review_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('admin:volunteer_review', args=[self.place.pk]))
        self.assertEqual([row.pk for row in response.context['page']], [place_revision.pk])
        self.assertEqual(VolunteerPlaceRevision.objects.filter(status='pending').count(), 2)
        program_revision.refresh_from_db()
        self.assertEqual(program_revision.status, 'pending')
        self.assertEqual(program_revision.payload, {'description_az': 'Pending program description'})
