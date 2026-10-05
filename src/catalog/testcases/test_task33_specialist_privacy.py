"""Person documents must never inherit general staff or public-media access."""
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import Permission, Group
from django.utils import timezone
from django.urls import reverse

from catalog.models import Specialist, SpecialistDocument
from catalog.views import serve_specialist_document
from config.views import serve_media_file


class SpecialistPrivateBoundaryTests(TestCase):
    @staticmethod
    def close_stream(response):
        # Direct RequestFactory responses do not have TestClient's signal isolation.
        # Close file handles without emitting request_finished inside TestCase.atomic.
        for closer in response._resource_closers:
            closer()
    def setUp(self):
        self.public = TemporaryDirectory()
        self.private = TemporaryDirectory()
        self.addCleanup(self.public.cleanup)
        self.addCleanup(self.private.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.public.name, PRIVATE_MEDIA_ROOT=self.private.name,
                                         SPECIALISTS_SECTION_ENABLED=True)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.owner = get_user_model().objects.create_user('private-person')
        from catalog.models import SiteSettings
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.staff = get_user_model().objects.create_user('ordinary-staff', is_staff=True)
        self.person = Specialist.objects.create(name='Synthetic Person', owner=self.owner)
        self.doc = SpecialistDocument.objects.create(specialist=self.person, document_type='identity',
                    name='Synthetic identity', file=SimpleUploadedFile('proof.txt', b'only synthetic bytes'))

    def test_ordinary_staff_cannot_download_identity(self):
        request = RequestFactory().get('/synthetic-document')
        request.user = self.staff
        with self.assertRaises(Http404):
            serve_specialist_document(request, self.doc.pk)

    def test_private_storage_has_no_public_url(self):
        with self.assertRaises(ValueError):
            _ = self.doc.file.url

    def test_document_bytes_are_outside_public_media(self):
        from pathlib import Path
        self.assertFalse(Path(self.doc.file.path).is_relative_to(Path(self.public.name)))

    def test_direct_legacy_media_download_is_denied(self):
        from pathlib import Path
        path = Path(self.public.name) / 'protected_docs/specialists/legacy.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'synthetic legacy evidence')
        request = RequestFactory().get('/media/protected_docs/specialists/legacy.txt')
        with self.assertRaises(Http404):
            serve_media_file(request, 'protected_docs/specialists/legacy.txt')

    def verified(self):
        self.person.verified_person_user = self.owner
        self.person.person_verified_at = timezone.now()
        self.person.status = 'published'
        self.person.save()

    def download(self, user):
        request = RequestFactory().get('/synthetic-document')
        request.user = user
        response = serve_specialist_document(request, self.doc.pk)
        self.addCleanup(self.close_stream, response)
        return response

    def test_legacy_management_owner_is_not_verified_person(self):
        with self.assertRaises(Http404):
            self.download(self.owner)

    def test_verified_person_can_read_private_identity_as_attachment(self):
        self.verified()
        response = self.download(self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'only synthetic bytes')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_dedicated_reviewer_permission_and_revocation(self):
        self.staff.user_permissions.add(Permission.objects.get(codename='review_specialist_documents'))
        self.assertEqual(self.download(self.staff).status_code, 200)
        self.staff.user_permissions.clear()
        with self.assertRaises(Http404):
            self.download(self.staff)

    def test_volunteer_with_accidental_permission_is_denied(self):
        from catalog.services.staff_roles import VOLUNTEER_GROUP
        self.staff.user_permissions.add(Permission.objects.get(codename='review_specialist_documents'))
        self.staff.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        with self.assertRaises(Http404):
            self.download(self.staff)

    def test_approved_certificate_without_person_opt_in_stays_private(self):
        self.verified()
        self.doc = SpecialistDocument.objects.create(specialist=self.person, document_type='certificate',
            name='Synthetic qualification', file=SimpleUploadedFile('certificate.pdf', b'%PDF-synthetic'),
            status='approved', is_published=True)
        from django.contrib.auth.models import AnonymousUser
        with self.assertRaises(Http404):
            self.download(AnonymousUser())

    def test_identity_cannot_become_public_even_with_tampered_flags(self):
        self.verified()
        self.doc.status = 'approved'
        self.doc.is_published = True
        self.doc.opted_in_by = self.owner
        self.doc.opted_in_at = timezone.now()
        self.doc.save()
        from django.contrib.auth.models import AnonymousUser
        with self.assertRaises(Http404):
            self.download(AnonymousUser())

    def test_foreign_document_id_denied_to_verified_person(self):
        self.verified()
        foreign = get_user_model().objects.create_user('foreign-private-person')
        with self.assertRaises(Http404):
            self.download(foreign)

    def test_debug_media_route_uses_same_guard(self):
        from pathlib import Path
        from importlib import reload
        import config.urls
        path = Path(self.public.name) / 'protected_docs/specialists/direct.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'synthetic direct URL')
        with override_settings(DEBUG=True, SERVE_MEDIA_FILES=True):
            reload(config.urls)
            try:
                self.assertEqual(self.client.get('/media/protected_docs/specialists/direct.txt').status_code, 404)
                # A normal public photo/file must remain reachable.
                (Path(self.public.name) / 'public.txt').write_bytes(b'public synthetic')
                response = self.client.get('/media/public.txt')
                self.assertEqual(response.status_code, 200)
                self.close_stream(response)
            finally:
                reload(config.urls)

    def test_retired_location_history_is_not_public_current_practice(self):
        self.verified()
        from catalog.models import SpecialistPracticeLocation
        location = SpecialistPracticeLocation.objects.create(specialist=self.person,
            address='Synthetic retired private office', is_active=False, lat=40.123456, lng=49.654321)
        response = self.client.get(reverse('specialist_detail', args=[self.person.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Synthetic retired private office')
        self.assertNotContains(response, '40.123456')
        self.assertTrue(SpecialistPracticeLocation.objects.filter(pk=location.pk).exists())

    def test_retired_location_cannot_match_public_region_filter(self):
        self.verified()
        from catalog.models import SpecialistPracticeLocation, Region
        region = Region.objects.create(key='retired-private-region', name_az='Synthetic retired region',
                                       name_ru='Synthetic retired region', name_en='Synthetic retired region')
        SpecialistPracticeLocation.objects.create(specialist=self.person, region=region,
            address='Synthetic retired office', is_active=False)
        response = self.client.get(reverse('specialist_list'), {'region': region.pk})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.person.pk, [item.pk for item in response.context['page_obj']])
