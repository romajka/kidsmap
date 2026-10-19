"""Rendered review must explain decisions and show the proposed gallery."""
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import PlacePhoto, VolunteerPlaceRevision, WorkflowNotification
from catalog.services import publication
from catalog.testcases.image_uploads import build_image_upload
from catalog.testcases.utils import create_quality_place


class OwnerModerationPresentationTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory(); self.addCleanup(media.cleanup)
        configured = override_settings(MEDIA_ROOT=media.name)
        configured.enable(); self.addCleanup(configured.disable)
        users = get_user_model()
        self.owner = users.objects.create_user('long_owner_' + 'a' * 110)
        self.staff = users.objects.create_superuser('gallery_reviewer', 'reviewer@example.invalid', 'synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        storage = PlacePhoto._meta.get_field('image').storage
        self.first = storage.save('places/gallery/first.png', build_image_upload('first.png'))
        self.second = storage.save('places/gallery/second.png', build_image_upload('second.png'))
        self.revision = publication.propose(
            actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'gallery': [
                {'id': None, 'image': self.second, 'caption': 'Second image', 'order': 0},
                {'id': None, 'image': self.first, 'caption': 'First image', 'order': 1},
            ]}, schema_version=1, expected_version=self.place.content_version)
        self.url = reverse('admin:volunteer_review', args=[self.place.pk])
        self.client.force_login(self.staff)

    def test_review_shows_gallery_thumbnails_in_proposed_order_without_writes(self):
        for path, label in [(self.url, 'Qalereya'), ('/ru' + self.url, 'Галерея'), ('/en' + self.url, 'Gallery')]:
            with self.subTest(path=path):
                # Unprefixed admin intentionally defaults to RU; select AZ explicitly.
                self.client.cookies['django_language'] = 'az'
                response = self.client.get(path)
                self.assertContains(response, label)
                self.assertContains(response, 'src="/media/' + self.first + '"')
                self.assertContains(response, 'src="/media/' + self.second + '"')
                html = response.content.decode()
                self.assertLess(html.index('src="/media/' + self.second), html.index('src="/media/' + self.first))
                self.assertNotContains(response, "&#x27;image&#x27;:")
        self.assertFalse(self.place.gallery.exists())
        self.revision.refresh_from_db()
        self.assertEqual((self.revision.status, self.revision.version), ('pending', 1))

    def test_nature_uses_a_human_label(self):
        from catalog.domain_admin.volunteer import display_value
        for lang, expected in [('az', 'Biznes'), ('ru', 'Бизнес'), ('en', 'Business')]:
            with self.subTest(lang=lang), override(lang):
                self.assertEqual(display_value('nature', 'business'), expected)

    def test_gallery_paths_cannot_turn_into_external_or_traversal_previews(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'gallery': [
            {'image': 'https://untrusted.invalid/a.png', 'order': 0},
            {'image': '../private/a.png', 'order': 1},
        ]})
        response = self.client.get('/ru' + self.url)
        self.assertNotContains(response, 'https://untrusted.invalid')
        self.assertNotContains(response, '../private/')
        self.assertEqual(response.status_code, 200)

    def test_empty_rejection_reason_is_localized_and_does_not_change_decision(self):
        for prefix, expected in [('', 'Qərarın səbəbini göstərin.'), ('/ru', 'Укажите причину решения.'), ('/en', 'Provide a decision reason.')]:
            with self.subTest(prefix=prefix):
                self.client.cookies['django_language'] = 'az'
                response = self.client.post(prefix + self.url, {'action': 'reject', 'version': 1})
                self.assertContains(response, expected)
                self.revision.refresh_from_db()
                self.assertEqual((self.revision.status, self.revision.version), ('pending', 1))
                self.assertFalse(WorkflowNotification.objects.exists())

    def test_nonstaff_cannot_get_gallery_comparison(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(response, self.first, status_code=302)

    def test_gallery_caption_is_escaped(self):
        payload = self.revision.payload.copy()
        payload['gallery'][0]['caption'] = '<img src=x onerror=alert(1)>'
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload=payload)
        response = self.client.get('/ru' + self.url)
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')

    def test_removed_gallery_has_an_explicit_empty_state(self):
        PlacePhoto.objects.create(place=self.place, image=self.first, order=0)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'gallery': []})
        response = self.client.get('/en' + self.url)
        self.assertContains(response, 'No photos')
        self.assertContains(response, 'src="/media/' + self.first + '"')
        self.assertEqual(self.place.gallery.count(), 1)
