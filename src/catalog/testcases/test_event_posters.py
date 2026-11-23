"""Event posters: shape/colour facts, focus validation, session grouping, backfill."""
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from PIL import Image

from catalog.models import Category, Event, EventPhoto, SiteSettings
from catalog.services.event_images import clamp_focus, dominant_color, orientation_for
from catalog.services.event_sessions import by_day, group_sessions, session_key

BAKU = ZoneInfo('Asia/Baku')


def png(width, height, color=(200, 40, 90), margin=None):
    image = Image.new('RGB', (width, height), margin or color)
    if margin:
        image.paste(Image.new('RGB', (width // 2, height // 2), color), (width // 4, height // 4))
    out = BytesIO()
    image.save(out, 'PNG')
    return SimpleUploadedFile(f'p{width}x{height}.png', out.getvalue(), content_type='image/png')


class PosterFactsTests(SimpleTestCase):
    def test_orientation_thresholds(self):
        self.assertEqual(orientation_for(1240, 1754), 'portrait')    # A4
        self.assertEqual(orientation_for(1080, 1920), 'portrait')    # 9:16
        self.assertEqual(orientation_for(1080, 1080), 'square')
        self.assertEqual(orientation_for(1920, 1080), 'landscape')   # 16:9
        self.assertEqual(orientation_for(85, 100), 'square')         # 0.85 is not below the line
        self.assertEqual(orientation_for(84, 100), 'portrait')
        self.assertEqual(orientation_for(120, 100), 'square')        # 1.2 is not above the line
        self.assertEqual(orientation_for(121, 100), 'landscape')
        self.assertEqual(orientation_for(0, 100), '')
        self.assertEqual(orientation_for(None, None), '')

    def test_focus_is_clamped_for_display(self):
        self.assertEqual(clamp_focus(-5), 0)
        self.assertEqual(clamp_focus(140), 100)
        self.assertEqual(clamp_focus('33.6'), 34)
        self.assertEqual(clamp_focus('x'), 50)
        self.assertEqual(clamp_focus(None), 50)

    def test_dominant_colour_ignores_white_margins(self):
        poster = Image.new('RGB', (200, 300), (255, 255, 255))
        poster.paste(Image.new('RGB', (100, 150), (220, 30, 60)), (50, 75))
        color = dominant_color(poster)
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        self.assertGreater(r, 180)          # saturation weighting keeps the red
        self.assertLess(g, 120)


class EventPosterDataTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='poster', name_az='Poster')
        self.start = timezone.now() + timedelta(days=3)

    def event(self, **values):
        defaults = dict(name='Poster QA', name_az='Poster QA', category=self.category,
                        start_datetime=self.start, end_datetime=self.start + timedelta(hours=1),
                        status=Event.STATUS_PUBLISHED)
        defaults.update(values)
        return Event.objects.create(**defaults)

    def test_upload_stores_size_orientation_and_colour(self):
        event = self.event(photo=png(400, 561))
        event.refresh_from_db()
        self.assertEqual((event.photo_width, event.photo_height, event.photo_orientation), (400, 561, 'portrait'))
        self.assertRegex(event.photo_dominant_color, r'^#[0-9a-f]{6}$')
        photo = EventPhoto.objects.create(event=event, image=png(1920, 1080), order=1)
        photo.refresh_from_db()
        self.assertEqual(photo.orientation, 'landscape')
        # A replaced file is measured again.
        event.photo = png(1080, 1080)
        event.save()
        event.refresh_from_db()
        self.assertEqual(event.photo_orientation, 'square')

    def test_focus_must_stay_within_0_100(self):
        event = self.event()
        event.photo_focus_x = 101
        with self.assertRaises(ValidationError) as caught:
            event.full_clean(exclude=['photo'])
        self.assertIn('photo_focus_x', caught.exception.message_dict)
        photo = EventPhoto(event=event, image='events/gallery/x.png', focus_y=150)
        with self.assertRaises(ValidationError):
            photo.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.filter(pk=event.pk).update(photo_focus_y=250)

    def test_admin_gallery_form_accepts_missing_focus_and_rejects_out_of_range(self):
        from catalog.domain_admin.place_admin.forms import EventPhotoInlineForm
        event = self.event()
        files = {'image': png(300, 300)}
        form = EventPhotoInlineForm(data={'caption': '', 'order': 0}, files=files, instance=EventPhoto(event=event))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.cleaned_data['focus_x'], form.cleaned_data['focus_y']), (50, 50))
        bad = EventPhotoInlineForm(data={'caption': '', 'order': 0, 'focus_x': '-1', 'focus_y': '101'},
                                   files={'image': png(300, 300)}, instance=EventPhoto(event=event))
        self.assertFalse(bad.is_valid())
        self.assertIn('focus_x', bad.errors)
        self.assertIn('focus_y', bad.errors)

    def test_backfill_fills_old_rows_only(self):
        event = self.event(photo=png(1600, 900))
        Event.objects.filter(pk=event.pk).update(photo_width=None, photo_height=None, photo_orientation='', photo_dominant_color='')
        out = StringIO()
        call_command('backfill_event_image_meta', '--dry-run', stdout=out)
        self.assertIn('events: 1 to process', out.getvalue())
        call_command('backfill_event_image_meta', stdout=StringIO())
        event.refresh_from_db()
        self.assertEqual((event.photo_width, event.photo_orientation), (1600, 'landscape'))
        out = StringIO()
        call_command('backfill_event_image_meta', '--dry-run', stdout=out)
        self.assertIn('events: 0 to process', out.getvalue())

    def test_event_page_shows_sessions_and_whole_poster(self):
        place_values = dict(venue_label='Kukla Teatrı', address='Neftçilər 36')
        day = datetime(2031, 11, 29, tzinfo=BAKU)
        sessions = [self.event(photo=png(400, 561), start_datetime=day.replace(hour=h), end_datetime=day.replace(hour=h + 1), **place_values)
                    for h in (12, 14, 16)]
        response = self.client.get(sessions[1].get_absolute_url())
        self.assertContains(response, 'km-fit--whole')
        self.assertContains(response, 'event-poster--portrait')
        self.assertContains(response, 'aria-current="true"', count=1)
        for other in sessions:
            self.assertContains(response, other.get_absolute_url())
        self.assertContains(response, 'data-km-lb')


class SessionGroupingTests(SimpleTestCase):
    now = datetime(2031, 11, 25, 10, tzinfo=BAKU)

    def ev(self, pk, name, day, hour, *, place=7, hours=1, **extra):
        start = datetime(2031, 11, day, hour, tzinfo=BAKU)
        values = dict(pk=pk, name=name, name_az=name, name_ru='', name_en='', start_datetime=start,
                      end_datetime=start + timedelta(hours=hours), event_format='physical', related_place_id=place,
                      venue_snapshot={}, venue_label='', address='', organizer_organization_id=3,
                      organizer_specialist_id=None, occurrence_state='scheduled')
        values.update(extra)
        return SimpleNamespace(**values, get_absolute_url=lambda pk=pk: f'/event/{pk}/')

    def test_same_show_same_place_same_day_is_one_card(self):
        events = [self.ev(1, 'Qaraca qız', 29, 12), self.ev(2, 'Bremen', 29, 12), self.ev(3, 'Qaraca  qız ', 29, 14),
                  self.ev(4, 'Qaraca qız', 29, 16), self.ev(5, 'Qaraca qız', 30, 12),       # another day
                  self.ev(6, 'Qaraca qız', 29, 18, place=8)]                                 # another venue
        groups = group_sessions(events, now=self.now)
        self.assertEqual([g['event'].pk for g in groups], [1, 2, 5, 6])
        self.assertEqual([s['event'].pk for s in groups[0]['sessions']], [1, 3, 4])
        self.assertEqual([s['url'] for s in groups[0]['sessions']], ['/event/1/', '/event/3/', '/event/4/'])
        self.assertTrue(groups[0]['multi'])
        self.assertFalse(groups[1]['multi'])

    def test_long_running_events_are_never_grouped(self):
        long_a = self.ev(1, 'Sərgi', 26, 10, hours=24 * 30)
        long_b = self.ev(2, 'Sərgi', 26, 10, hours=24 * 30)
        self.assertIsNone(session_key(long_a))
        self.assertEqual(len(group_sessions([long_a, long_b], now=self.now)), 2)

    def test_by_day_puts_running_events_under_the_first_day(self):
        groups = group_sessions([self.ev(1, 'Sərgi', 20, 10, hours=24 * 30), self.ev(2, 'Teatr', 29, 12)], now=self.now)
        days = by_day(groups, now=self.now, first_day=datetime(2031, 11, 29).date())
        self.assertEqual([str(d['day']) for d in days], ['2031-11-29'])
        self.assertEqual(len(days[0]['groups']), 2)
