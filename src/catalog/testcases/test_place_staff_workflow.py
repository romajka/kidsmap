import json
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import VolunteerPlaceRevision, PlacePhoto
from catalog.testcases.utils import create_ready_place
from catalog.services.photo_gallery import gallery_key


class StaffGalleryWorkflowTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user('staff-gallery-volunteer', is_staff=True)
        group, _ = Group.objects.get_or_create(name='KidsMap Volunteers')
        self.user.groups.add(group)
        self.client.force_login(self.user)
        self.place = create_ready_place(created_by=self.user, owner=None)
        self.url = f'/admin/volunteer/{self.place.pk}/edit/'

    def image(self, name):
        stream = BytesIO()
        Image.new('RGB', (1200, 1200), 'green').save(stream, 'PNG')
        return SimpleUploadedFile(name, stream.getvalue(), 'image/png')

    def data(self, **overrides):
        response = self.client.get(self.url)
        form = response.context['form']
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name, field in form.fields.items() if not isinstance(field, forms.FileField)}
        data.update(action='draft', **overrides)
        return data

    def test_volunteer_has_optional_gallery_and_current_form_preview(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'name="gallery_images"')
        self.assertContains(response, reverse('admin_editor:volunteer_place_editor_preview', args=[self.place.pk]))
        self.assertContains(response, 'data-km-preview')
        self.assertNotRegex(response.content.decode(), r'Главное фото</?[^>]*>.*km-pf-field__required')

    def test_gallery_draft_reopens_without_publishing_and_preserves_omitted_gallery(self):
        payload = self.data(gallery_images=[self.image('first.png'), self.image('second.png')])
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        rows = revision.payload.get('gallery', [])
        self.assertEqual(len(rows), 2)
        self.assertEqual(self.place.gallery.count(), 0)
        reopened = self.client.get(self.url)
        self.assertEqual(len(reopened.context['editor_gallery']), 2)
        data = self.data(name_az='Changed gallery title')
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        revision.refresh_from_db()
        self.assertEqual(revision.payload['gallery'], rows)

    def test_gallery_can_remove_candidate_and_reorder_using_current_keys(self):
        response = self.client.post(self.url, self.data(gallery_images=[self.image('first.png'), self.image('second.png')]))
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        rows = revision.payload.get('gallery', [])
        self.assertEqual(len(rows), 2)
        payload = self.data(delete_gallery_ids=[gallery_key(rows[0])], gallery_order=json.dumps([gallery_key(rows[1])]))
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
        revision.refresh_from_db()
        self.assertEqual(len(revision.payload['gallery']), 1)
        self.assertEqual(revision.payload['gallery'][0]['image'], rows[1]['image'])

    def test_foreign_gallery_deletion_is_rejected_before_proposal(self):
        other = create_ready_place(name_az='Other gallery')
        photo = PlacePhoto.objects.create(place=other, image='other-gallery.webp')
        response = self.client.post(self.url, self.data(delete_gallery_ids=[str(photo.pk)]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('delete_gallery_ids', response.context['form'].errors)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
        self.assertTrue(PlacePhoto.objects.filter(pk=photo.pk).exists())

    def test_gallery_only_change_invalidates_an_older_editing_tab(self):
        payload = self.data(name_az='Old tab edit')
        PlacePhoto.objects.create(place=self.place, image='concurrent-gallery.webp')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['form'].errors)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
