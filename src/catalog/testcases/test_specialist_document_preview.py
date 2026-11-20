from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image, PngImagePlugin
from pypdf import PdfWriter

from catalog.models import SiteSettings, Specialist, SpecialistDocument


class SpecialistDocumentPreviewTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        settings = override_settings(PRIVATE_MEDIA_ROOT=media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.owner = get_user_model().objects.create_user('synthetic-document-person')
        self.person = Specialist.objects.create(
            name='Sample educator', slug='sample-documents', is_active=True, status='published',
            verified_person_user=self.owner, person_verified_at=timezone.now(),
        )

    def document(self, content, kind='diploma', **changes):
        fields = dict(name='Sample document', status='approved', is_published=True,
                      opted_in_by=self.owner, opted_in_at=timezone.now())
        fields.update(changes)
        return SpecialistDocument.objects.create(specialist=self.person, document_type=kind,
            file=SimpleUploadedFile('sample.bin', content), **fields)

    @staticmethod
    def pdf():
        writer = PdfWriter()
        writer.add_blank_page(width=660, height=400)
        writer.add_blank_page(width=400, height=660)
        stream = BytesIO()
        writer.write(stream)
        return stream.getvalue()

    def urls(self, doc):
        base = f'/ru/specialists/documents/{doc.pk}/preview/'
        return base, base + '1/'

    def test_gallery_links_to_paged_viewer_and_only_raster_reaches_browser(self):
        doc = self.document(self.pdf())
        viewer, page = self.urls(doc)
        profile = self.client.get('/ru/specialists/sample-documents/')
        self.assertContains(profile, f'href="{viewer}"')
        self.assertContains(profile, 'data-document-dialog')
        second = self.client.get(viewer, {'page': 2})
        self.assertContains(second, 'Sample document')
        self.assertContains(second, '2 / 2')
        self.assertContains(second, 'href="?page=1"')
        self.assertNotContains(second, 'href="?page=3"')
        self.assertIn('no-store', second['Cache-Control'])
        image = self.client.get(viewer + '2/')
        self.assertEqual(image['Content-Type'], 'image/jpeg')
        self.assertEqual(image['X-Content-Type-Options'], 'nosniff')
        with Image.open(BytesIO(image.content)) as rendered:
            self.assertGreater(rendered.height, rendered.width)
        self.assertEqual(self.client.get(viewer + '3/').status_code, 404)
        self.assertEqual(self.client.get(viewer, {'page': '-1'}).status_code, 404)

    def test_png_preview_removes_original_metadata_and_thumbnail_is_smaller(self):
        stream = BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('TeacherComment', 'PRIVATE_ORIGINAL_NOTE')
        Image.new('RGBA', (1100, 900), (123, 10, 42, 0)).save(stream, 'PNG', pnginfo=metadata)
        doc = self.document(stream.getvalue())
        _, page = self.urls(doc)
        response = self.client.get(page, {'thumb': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'PRIVATE_ORIGINAL_NOTE', response.content)
        with Image.open(BytesIO(response.content)) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLess(image.width, 700)
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_withdrawal_closes_warmed_preview_and_all_pages(self):
        doc = self.document(self.pdf())
        viewer, page = self.urls(doc)
        self.assertEqual(self.client.get(page).status_code, 200)
        SpecialistDocument.objects.filter(pk=doc.pk).update(is_published=False)
        for path in (viewer, page, viewer + '2/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertIn('no-store', response['Cache-Control'])
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(page).status_code, 200)

    def test_pending_and_identity_are_excluded_from_gallery_and_private_preview_acl(self):
        pending = self.document(self.pdf(), status='pending')
        identity = self.document(self.pdf(), kind='identity')
        for doc in (pending, identity):
            for url in self.urls(doc):
                self.assertEqual(self.client.get(url).status_code, 404)
        profile = self.client.get('/ru/specialists/sample-documents/')
        self.assertNotContains(profile, 'data-document-dialog')
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.urls(pending)[1]).status_code, 200)
        self.assertEqual(self.client.get(self.urls(identity)[1]).status_code, 404)

    def test_unrenderable_document_has_accessible_original_attachment_fallback(self):
        doc = self.document(b'invalid historical bytes')
        viewer, image = self.urls(doc)
        response = self.client.get(viewer)
        self.assertContains(response, 'Скачать оригинал')
        self.assertNotContains(response, '<img')
        self.assertEqual(self.client.get(image).status_code, 404)

    def test_pretransition_file_never_enters_viewer_or_public_download(self):
        doc = self.document(self.pdf())
        original_name = doc.file.name
        SpecialistDocument.objects.filter(pk=doc.pk).update(file='protected_docs/specialists/historical.pdf')
        try:
            viewer, page = self.urls(doc)
            for url in (viewer, page, viewer.replace('preview/', 'download/')):
                self.assertEqual(self.client.get(url).status_code, 404)
        finally:
            SpecialistDocument.objects.filter(pk=doc.pk).update(file=original_name)
