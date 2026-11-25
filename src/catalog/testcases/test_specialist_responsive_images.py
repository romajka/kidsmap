from html.parser import HTMLParser
from io import BytesIO, StringIO
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override
from PIL import Image

from catalog.models import (
    Organization, SiteSettings, Specialist, SpecialistPracticeLocation, SpecialistProposalDocument,
    SpecialistProposalDraft,
)
from catalog.models.specialist_domain import SpecialistEmployment
from catalog.private_storage import specialist_private_storage
from catalog.services.responsive_images import responsive_image
from catalog.testcases.utils import create_quality_place


class Images(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.photos = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.photos.append(dict(attrs))


def png():
    stream = BytesIO()
    Image.new('RGB', (2000, 2000), '#967058').save(stream, format='PNG')
    return stream.getvalue()


class SpecialistPortraitTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.media = Path(directory.name) / 'public'
        self.enterContext(override_settings(MEDIA_ROOT=self.media, PRIVATE_MEDIA_ROOT=Path(directory.name) / 'private'))
        self.enterContext(override('ru'))
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.organizations_section_enabled = True
        site.save()

    def person(self, file, **overrides):
        fields = dict(name='Portrait fixture', status=Specialist.STATUS_PUBLISHED, is_active=True, is_home_featured=True)
        with self.captureOnCommitCallbacks(execute=True):
            return Specialist.objects.create(photo=file, **(fields | overrides))

    def portraits(self, path, person):
        page = self.client.get(path)
        self.assertEqual(page.status_code, 200)
        sources = {person.photo.url, responsive_image(person.photo, portrait=True)['preview']}
        return [img for img in Images(page.content.decode()).photos if img.get('src') in sources]

    def test_public_pages_serve_sized_webp_portraits(self):
        person = self.person(ContentFile(png(), name='portrait.png'))
        for path in ['/ru/', '/ru/specialists/', person.get_absolute_url()]:
            with self.subTest(path=path):
                photos = self.portraits(path, person)
                self.assertTrue(photos)
                for img in photos:
                    self.assertIn('.webp', img['src'])
                    self.assertTrue(img.get('sizes'))
                    self.assertTrue(int(img['width']) > 0 and int(img['height']) > 0)
                    self.assertIn('.webp 320w', img['srcset'])
                    if path == '/ru/':
                        self.assertEqual(img.get('loading'), 'lazy')
                    else:
                        self.assertNotEqual(img.get('loading'), 'lazy')

    def test_undecodable_file_uses_original(self):
        person = self.person(ContentFile(b'not a decodable image', name='broken.heic'))
        for path in ['/ru/', '/ru/specialists/', person.get_absolute_url()]:
            with self.subTest(path=path):
                photos = self.portraits(path, person)
                self.assertTrue(photos)
                for img in photos:
                    self.assertEqual(img['src'], person.photo.url)
                    self.assertNotIn('srcset', img)
                    self.assertTrue(img.get('width') and img.get('height'))

    def test_backfill_and_publication_only_process_public_photos(self):
        self.enterContext(patch('catalog.management.commands.generate_responsive_images.static_photo',
                                side_effect=AssertionError('unrelated static photo read')))
        actor = get_user_model().objects.create_user(username='portrait-fixture')
        self.enterContext(patch.object(specialist_private_storage, 'open', side_effect=AssertionError('private photo read')))
        proposal = SpecialistProposalDraft.objects.create(actor=actor, photo=ContentFile(png(), name='private.png'))
        SpecialistProposalDocument.objects.create(
            draft=proposal, name='certificate', file=ContentFile(png(), name='certificate.png'),
        )
        draft = self.person(ContentFile(png(), name='draft.png'), status=Specialist.STATUS_DRAFT)
        person = self.person(None)
        person.photo.save('existing.png', ContentFile(png()), save=False)
        Specialist.objects.filter(pk=person.pk).update(photo=person.photo.name)
        root = self.media / 'responsive-images'
        call_command('generate_responsive_images', '--specialists-only', stdout=StringIO())
        self.assertFalse(root.exists())
        call_command('generate_responsive_images', '--specialists-only', apply=True, stdout=StringIO())
        self.assertEqual(len(list(root.rglob('manifest.json'))), 1)
        mtimes = {p: p.stat().st_mtime_ns for p in root.rglob('*') if p.is_file()}
        call_command('generate_responsive_images', '--specialists-only', apply=True, stdout=StringIO())
        self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in root.rglob('*') if p.is_file()})
        draft.status = Specialist.STATUS_PUBLISHED
        with self.captureOnCommitCallbacks(execute=True):
            draft.save(update_fields=['status'])
        self.assertEqual(len(list(root.rglob('manifest.json'))), 2)

    def test_detailed_portrait_candidates_fit_the_mobile_budget(self):
        texture = Random(42).randbytes(640 * 640 * 4)
        photo = Image.frombytes('RGBA', (640, 640), texture).resize((2000, 2000), Image.Resampling.NEAREST)
        data = BytesIO()
        photo.save(data, format='PNG')
        person = self.person(ContentFile(data.getvalue(), name='detailed.png'))
        img = self.portraits('/ru/', person)[0]
        self.assertTrue(img.get('srcset'))
        for candidate in img['srcset'].split(', '):
            url, width = candidate.rsplit(' ', 1)
            file = self.media / url.removeprefix('/media/')
            self.assertLessEqual(file.stat().st_size, 80_000)
            with Image.open(file) as decoded:
                self.assertEqual(width, f'{decoded.width}w')

    def test_teaser_rail_and_affiliated_profiles_use_the_portrait(self):
        owner = get_user_model().objects.create_user(username='portrait-owner')
        actor = get_user_model().objects.create_user(username='portrait-person')
        person = self.person(ContentFile(png(), name='linked.png'), is_home_featured=False,
                             offers_office=True, verified_person_user=actor, person_verified_at=timezone.now())
        place = create_quality_place()
        SpecialistPracticeLocation.objects.create(specialist=person, place=place)
        org = Organization.objects.create(name_az='Portrait org', status='published', approved_at=timezone.now(), owner=owner)
        SpecialistEmployment.objects.create(
            specialist=person, organization=org, role='Teacher', start_date=timezone.localdate(),
            status=SpecialistEmployment.ACTIVE, person_user=actor, person_confirmed_by=actor,
            person_confirmed_at=timezone.now(), organization_owner=owner, organization_confirmed_by=owner,
            organization_confirmed_at=timezone.now(), organization_ownership_version=org.ownership_version,
        )
        for path in ('/ru/', place.get_absolute_url(), reverse('organization_detail', args=[org.public_id])):
            with self.subTest(path=path):
                imgs = self.portraits(path, person)
                self.assertTrue(imgs)
                self.assertTrue(all(img.get('srcset') and img.get('sizes') and img.get('width')
                                    and img.get('height') and img.get('loading') == 'lazy' for img in imgs))
        for n in range(5):
            self.person(person.photo.name, name=f'Rail fixture {n}', is_home_featured=False)
        rail = self.client.get('/ru/')
        self.assertEqual(rail.context['home_specialists']['mode'], 'rail')
        self.assertEqual(sum(bool(img.get('srcset')) for img in self.portraits('/ru/', person)), 6)
        cards = self.portraits('/ru/specialists/', person)
        self.assertEqual(len(cards), 6)
        self.assertNotEqual(cards[0].get('loading'), 'lazy')
        self.assertTrue(all(img.get('loading') == 'lazy' for img in cards[1:]))

    def test_admin_bulk_publish_prepares_approved_portrait(self):
        self.client.force_login(get_user_model().objects.create_superuser(username='portrait-admin'))
        person = self.person(ContentFile(png(), name='moderated.png'), status=Specialist.STATUS_DRAFT,
                             offers_online=True, consultation_format='online', lesson_type='individual', lesson_price=25)
        self.assertFalse((self.media / 'responsive-images').exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('admin:catalog_specialist_changelist'),
                             {'action': 'mark_published', '_selected_action': [person.pk]})
        person.refresh_from_db()
        self.assertEqual(person.status, Specialist.STATUS_PUBLISHED)
        self.assertIn('.webp', self.portraits('/ru/specialists/', person)[0]['src'])
