"""Six demo events whose posters and gallery photos come in every shape.

For local development only: lets you see how the event page handles a stage
photo, an A4 poster, an Instagram square, a 9:16 story, a panorama and an old
photo without stored size. Refuses to run unless DEBUG is on. Only touches
events with the six numbered demo slugs.

    python manage.py seed_demo_event_posters           # create (or recreate) them
    python manage.py seed_demo_event_posters --delete  # remove them and their files
"""
from __future__ import annotations

import io
import math
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from catalog.models import Category, Event, EventPhoto
from catalog.services.responsive_images import _directory as responsive_image_directory

PREFIX = 'demo-afisha-'

# sky top, sky bottom, sun, hills, accent — warm, child-friendly, varied
PALETTES = {
    'night': ('#0b1f4a', '#1d5a8c', '#f6d36b', '#0e5a63', '#ffffff'),
    'sunset': ('#ffb36b', '#ff6f61', '#fff3c4', '#7a2e4a', '#ffe08a'),
    'meadow': ('#bfe6ff', '#e8f7ff', '#ffd23f', '#3fa36b', '#ffffff'),
    'candy': ('#ffd1e8', '#fff0f7', '#ff8fb1', '#8e6bd6', '#ffffff'),
    'sea': ('#6fd3ff', '#d4f4ff', '#ffe066', '#1f7a9c', '#ffffff'),
    'stage': ('#1b0f1f', '#3a1730', '#ffe9a8', '#8a4b22', '#c21d35'),
}


def _font(size: int):
    for name in ('DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                 'arialbd.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def picture(width: int, height: int, palette: str, label: str) -> bytes:
    """A cheerful illustrated scene with the shape written on it (e.g. '3:2 · 1800×1200')."""
    top, bottom, sun, hills, accent = PALETTES[palette]
    img = Image.new('RGB', (width, height), top)
    d = ImageDraw.Draw(img)
    t, b = Image.new('RGB', (1, 1), top).getpixel((0, 0)), Image.new('RGB', (1, 1), bottom).getpixel((0, 0))
    for y in range(height):  # vertical gradient sky
        k = y / max(1, height - 1)
        d.line([(0, y), (width, y)], fill=tuple(round(t[i] + (b[i] - t[i]) * k) for i in range(3)))
    m = min(width, height)
    # soft glow + sun
    glow = Image.new('L', (width, height), 0)
    cx, cy, r = width * .68, height * .34, m * .2
    ImageDraw.Draw(glow).ellipse((cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2), fill=120)
    img.paste(Image.new('RGB', (width, height), sun), (0, 0), glow.filter(ImageFilter.GaussianBlur(m * .08)))
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=sun)
    # two layers of rolling hills
    for layer, (base, amp, shade) in enumerate(((.70, .06, 0), (.80, .05, 28))):
        pts = [(0, height)]
        for x in range(0, width + 20, 20):
            pts.append((x, height * base + math.sin(x / width * math.pi * (3 + layer) + layer) * height * amp))
        pts.append((width, height))
        rgb = Image.new('RGB', (1, 1), hills).getpixel((0, 0))
        d.polygon(pts, fill=tuple(max(0, c - shade) for c in rgb))
    # confetti dots
    for i in range(18):
        x = (i * 0.618 % 1) * width
        y = ((i * 0.381 + .07) % .55) * height
        rr = m * (.008 + (i % 3) * .004)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=accent)
    # label pill: the shape of the picture, so you can see what you are looking at
    font = _font(max(18, round(m * .075)))
    box = d.textbbox((0, 0), label, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad = th * .7
    x0, y0 = (width - tw) / 2 - pad, height * .86 - th / 2 - pad
    d.rounded_rectangle((x0, y0, x0 + tw + pad * 2, y0 + th + pad * 2), radius=round(th), fill='#ffffff')
    d.text((x0 + pad - box[0], y0 + pad - box[1]), label, font=font, fill='#11472b')
    out = io.BytesIO()
    img.save(out, 'JPEG', quality=88, optimize=True)
    return out.getvalue()


def shot(w, h, palette, ratio_label):
    return {'w': w, 'h': h, 'palette': palette, 'label': f'{ratio_label} · {w}×{h}'}


# name, description of what to look at, poster, gallery, extra settings
DEMOS = [
    ('Демо: горизонтальное фото со сцены', 'Фото со сцены 3:2 и галерея из шести фото всех форматов.',
     shot(1800, 1200, 'stage', '3:2'),
     [shot(1240, 1754, 'night', 'A4'), shot(1920, 1080, 'meadow', '16:9'), shot(1080, 1080, 'candy', '1:1'),
      shot(2520, 1080, 'sea', '21:9'), shot(1080, 1920, 'sunset', '9:16'), shot(1200, 1500, 'meadow', '4:5')], {}),
    ('Демо: вертикальная афиша A4', 'Классическая афиша A4 — встаёт рядом с заголовком.',
     shot(1240, 1754, 'night', 'A4'), [shot(1600, 1200, 'meadow', '4:3'), shot(1200, 1600, 'candy', '3:4')], {}),
    ('Демо: квадратный пост из Instagram', 'Квадрат 1:1 без галереи.',
     shot(1080, 1080, 'candy', '1:1'), [], {}),
    ('Демо: сторис 9:16', 'Очень высокая картинка из сторис.',
     shot(1080, 1920, 'sunset', '9:16'), [shot(1920, 1080, 'sea', '16:9')], {}),
    ('Демо: панорама 3:1', 'Шире 2:1 — рамка 2:1, по краям размытая копия.',
     shot(2400, 800, 'sea', '3:1'), [shot(2400, 800, 'meadow', '3:1'), shot(1080, 1080, 'candy', '1:1'), shot(1240, 1754, 'night', 'A4')], {}),
    ('Демо: старое фото без размеров', 'Так выглядят афиши, пока на сервере не запущен backfill_event_image_meta.',
     shot(1920, 1080, 'meadow', '16:9'), [], {'wipe_meta': True}),
]


class Command(BaseCommand):
    help = 'Create demo events with posters and gallery photos of every shape (DEBUG only).'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Remove the demo events and their files.')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Only for local development: run with DJANGO_DEBUG=1.')
        removed = self._delete()
        if options['delete']:
            self.stdout.write(self.style.SUCCESS(f'Removed {removed} demo events.'))
            return

        category = (Category.objects.filter(code__in=Event.objects.values('category')).order_by('order').first()
                    or Category.objects.filter(is_active=True).order_by('order').first())
        if category is None:
            raise CommandError('No categories yet: run seed_catalog_taxonomy first.')

        now = timezone.now()
        base = now.replace(hour=12, minute=0, second=0, microsecond=0)
        urls = []
        for n, (name, note, poster, gallery, extra) in enumerate(DEMOS, start=1):
            start = base + timedelta(days=2 + n)
            slug = f'{PREFIX}{n}'
            with transaction.atomic():
                event = Event.objects.create(
                    name=name, name_ru=name, name_az=name, name_en=name, slug=slug,
                    description_ru=note, description_az=note, description_en=note,
                    category=category, start_datetime=start, end_datetime=start + timedelta(hours=1, minutes=30),
                    age_from=3, age_to=10, price_text='10 AZN',
                    venue_label='Демо-площадка KidsMap', address='Bakı, Nizami küçəsi 1',
                    status=Event.STATUS_PUBLISHED, published_at=now,
                    photo=ContentFile(picture(poster['w'], poster['h'], poster['palette'], poster['label']), name=f'{slug}.jpg'),
                )
                # Event.save() removes digits from public slugs. Keep the fixed local demo URLs.
                Event.objects.filter(pk=event.pk).update(slug=slug)
                event.slug = slug
            for i, g in enumerate(gallery):
                EventPhoto.objects.create(
                    event=event, order=i, caption=f'Фото {g["label"]}',
                    image=ContentFile(picture(g['w'], g['h'], g['palette'], g['label']), name=f'{slug}-{i + 1}.jpg'))
            if extra.get('wipe_meta'):
                Event.objects.filter(pk=event.pk).update(photo_width=None, photo_height=None,
                                                         photo_orientation='', photo_dominant_color='')
            urls.append((name, event.get_absolute_url()))

        self.stdout.write(self.style.SUCCESS(f'Created {len(urls)} demo events (category "{category.code}"):'))
        for name, url in urls:
            self.stdout.write(f'  {name}\n    http://127.0.0.1:8000{url}')
        try:
            from catalog.models import SiteSettings
            if not SiteSettings.get_solo().events_section_enabled:
                self.stdout.write(self.style.WARNING('The events section is switched off in site settings: '
                                                     'turn it on in the admin to open these pages.'))
        except Exception:  # noqa: BLE001 - only a hint
            pass

    def _delete(self) -> int:
        slugs = [f'{PREFIX}{n}' for n in range(1, len(DEMOS) + 1)]
        events = list(Event.objects.filter(slug__in=slugs).prefetch_related('gallery'))
        Event.objects.filter(pk__in=[event.pk for event in events]).delete()
        for event in events:
            for photo in event.gallery.all():
                self._delete_image(photo.image)
            self._delete_image(event.photo)
        return len(events)

    @staticmethod
    def _delete_image(image):
        if not image or not image.storage.exists(image.name):
            return
        storage = image.storage
        directory = responsive_image_directory(image)
        if storage.exists(directory):
            _, filenames = storage.listdir(directory)
            for filename in filenames:
                storage.delete(f'{directory}/{filename}')
            storage.delete(directory)
        image.delete(save=False)
