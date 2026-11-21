from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from catalog.models import SiteSettings, Specialist, SpecialistClaim, SpecialistProposalDraft
from catalog.testcases.specialist_document_fixtures import image_document_bytes


class SpecialistMissingPhotoTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user('photo-applicant')
        self.client.force_login(self.actor)
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.person = Specialist.objects.create(name='Legacy application', created_by=self.actor,
                                                status=Specialist.STATUS_PENDING)
        self.proposal = SpecialistProposalDraft.objects.create(
            actor=self.actor, submitted_specialist=self.person, submitted_at=timezone.now(),
            payload={'profile_subject': ['self']})
        self.claim = SpecialistClaim.objects.create(applicant=self.actor, specialist=self.person)
        self.url = f'/ru/account/specialists/{self.person.pk}/add-photo/'

    def upload(self):
        return self.client.post(self.url, {'photo': SimpleUploadedFile('portrait.png', image_document_bytes()),
                                           'profile_status': self.person.status, 'name': 'Ignored change'})

    def test_approval_while_owner_is_choosing_photo_requires_reviewing_new_status(self):
        self.person.verified_person_user = self.actor
        self.person.person_verified_at = timezone.now()
        self.person.save()
        Specialist.objects.filter(pk=self.person.pk).update(status=Specialist.STATUS_PUBLISHED)
        self.assertEqual(self.upload().status_code, 409)
        self.person.refresh_from_db()
        self.assertEqual(self.person.status, Specialist.STATUS_PUBLISHED)
        self.assertFalse(self.person.photo)

    def test_pending_author_adds_only_missing_photo_without_resubmission(self):
        self.assertContains(self.client.get('/ru/account/specialists/'), self.url)
        self.assertEqual(self.upload().status_code, 302)
        self.person.refresh_from_db()
        self.assertTrue(self.person.photo.name.endswith('.webp'))
        self.assertEqual(self.person.name, 'Legacy application')
        self.assertEqual(self.person.status, Specialist.STATUS_PENDING)
        self.proposal.refresh_from_db()
        self.assertIsNotNone(self.proposal.submitted_at)
        self.assertNotContains(self.client.get('/ru/account/specialists/'), self.url)
        self.assertEqual(self.upload().status_code, 404)

    def test_only_own_pending_self_application_can_be_supplemented_before_verification(self):
        self.proposal.payload = {'profile_subject': ['other']}
        self.proposal.save()
        self.assertEqual(self.upload().status_code, 404)
        self.proposal.payload = {'profile_subject': ['self']}
        self.proposal.save()
        self.claim.status = SpecialistClaim.REJECTED
        self.claim.save()
        self.assertEqual(self.upload().status_code, 404)
        self.client.force_login(get_user_model().objects.create_user('different-applicant'))
        self.assertEqual(self.upload().status_code, 404)

    def test_published_profile_has_owner_link_and_keeps_existing_review_workflow(self):
        self.person.status = Specialist.STATUS_PUBLISHED
        self.person.save()
        self.assertEqual(self.upload().status_code, 404)
        self.person.verified_person_user = self.actor
        self.person.person_verified_at = timezone.now()
        self.person.save()
        self.assertContains(self.client.get('/ru/account/specialists/'), self.url)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.person.refresh_from_db()
        self.assertEqual(self.person.status, Specialist.STATUS_PUBLISHED)
        invalid = self.client.post(self.url, {'photo': SimpleUploadedFile('bad.jpg', b'bad'),
                                              'profile_status': self.person.status})
        self.assertEqual(invalid.status_code, 400)
        self.person.refresh_from_db()
        self.assertFalse(self.person.photo)
        self.assertEqual(self.person.status, Specialist.STATUS_PUBLISHED)
        self.assertEqual(self.upload().status_code, 302)
        self.person.refresh_from_db()
        self.assertEqual(self.person.status, Specialist.STATUS_PENDING)
        self.assertTrue(self.person.photo)
