"""Give published specialists without a photo an illustrated demo portrait.

For local development only: the home page and the specialist cards look very
different with portraits, and real photos only arrive with real profiles.
Refuses to run unless DEBUG is on. Never touches a specialist that already has
a photo unless --replace is given.

    python manage.py seed_demo_specialist_photos            # fill the gaps
    python manage.py seed_demo_specialist_photos --dry-run  # only list them
    python manage.py seed_demo_specialist_photos --replace  # also redraw demo pictures (demo-*)
"""
from __future__ import annotations

import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw, ImageFilter

from catalog.models import Specialist

# background, skin, hair, top — soft, varied, all on-brand enough to sit on a green site
PALETTES = [
    ("#dff2e6", "#f1c7a5", "#3b2a20", "#2f7d57"),
    ("#fde9d7", "#e8b48f", "#1f1a17", "#d0603f"),
    ("#e3ecfb", "#c98d68", "#2b1d16", "#3d6fb6"),
    ("#f6e3f0", "#f3d0b4", "#7a4a2a", "#a24b84"),
    ("#fff2cc", "#d9a07a", "#2d211b", "#c98a00"),
    ("#e1f3f4", "#b9805c", "#141110", "#1f8a8a"),
    ("#ece6fb", "#f0c8a8", "#5a3a28", "#6b54c4"),
    ("#e9f5dc", "#e2a982", "#3a2618", "#5b8a2e"),
]
W, H = 640, 800


def _portrait(index: int, long_hair: bool) -> bytes:
    bg, skin, hair, top = PALETTES[index % len(PALETTES)]
    scale = 2  # draw large, scale down: smooth edges
    w, h = W * scale, H * scale
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)

    # soft light disc behind the head
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).ellipse((w * .12, h * .08, w * .88, h * .70), fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(60 * scale))
    img.paste(Image.new("RGB", (w, h), "#ffffff"), (0, 0), glow)
    d = ImageDraw.Draw(img)

    cx = w / 2
    # shoulders / top
    d.rounded_rectangle((cx - w * .40, h * .645, cx + w * .40, h * 1.15), radius=int(w * .22), fill=top)
    # collar
    d.polygon([(cx - w * .09, h * .645), (cx + w * .09, h * .645), (cx, h * .735)], fill=skin)
    # long hair behind the head
    if long_hair:
        d.rounded_rectangle((cx - w * .22, h * .26, cx + w * .22, h * .69), radius=int(w * .16), fill=hair)
    # neck
    d.rounded_rectangle((cx - w * .075, h * .54, cx + w * .075, h * .66), radius=int(w * .05), fill=skin)
    # head
    d.ellipse((cx - w * .19, h * .22, cx + w * .19, h * .60), fill=skin)
    # hair on top
    d.chord((cx - w * .205, h * .19, cx + w * .205, h * .52), 180, 360, fill=hair)
    d.pieslice((cx - w * .21, h * .20, cx + w * .02, h * .44), 160, 290, fill=hair)
    # face: eyes, smile, cheeks
    eye_y = h * .41
    for dx in (-.07, .07):
        d.ellipse((cx + w * dx - 9 * scale, eye_y - 9 * scale, cx + w * dx + 9 * scale, eye_y + 9 * scale), fill="#2b2b2b")
    d.arc((cx - w * .07, h * .44, cx + w * .07, h * .53), 20, 160, fill="#8a4b3a", width=6 * scale)
    for dx in (-.115, .115):
        d.ellipse((cx + w * dx - 22 * scale, h * .465 - 12 * scale, cx + w * dx + 22 * scale, h * .465 + 12 * scale), fill="#f2a7a0")

    img = img.resize((W, H), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def _looks_female(name: str, n: int) -> bool:
    """Rough guess from the surname ending (Мамедова, Aliyeva, Huseynli → unknown)."""
    words = [w.strip(".,·—-").lower() for w in (name or "").split()]
    for word in reversed(words):
        if word.endswith(("ова", "ева", "ина", "ова", "ova", "eva", "yeva", "ina", "qızı", "kızı", "кызы")):
            return True
        if word.endswith(("ов", "ев", "ин", "ov", "ev", "yev", "in", "oğlu", "оглу")):
            return False
    return n % 2 == 0


class Command(BaseCommand):
    help = "Local development only: give published specialists without a photo an illustrated demo portrait."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list who would get a portrait.")
        parser.add_argument("--replace", action="store_true", help="Also redraw demo pictures (files named demo-*).")

    def handle(self, *args, dry_run=False, replace=False, **options):
        if not settings.DEBUG:
            raise CommandError("This command only runs with DEBUG on (local development). Nothing was changed.")
        qs = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True).order_by("pk")
        targets = []
        for person in qs:
            current = person.photo.name if person.photo else ""
            # --replace also redraws the placeholder silhouettes the demo data ships with
            is_demo = "demo-portrait-" in current or current.rsplit("/", 1)[-1].startswith("demo-")
            if not current or (replace and is_demo):
                targets.append(person)
        if not targets:
            self.stdout.write(self.style.SUCCESS("Every published specialist already has a photo."))
            return
        for n, person in enumerate(targets):
            if dry_run:
                self.stdout.write(f"would draw: #{person.pk} {person.name}")
                continue
            data = _portrait(person.pk, long_hair=_looks_female(person.name, n))
            if person.photo and "demo-portrait-" in person.photo.name:
                person.photo.delete(save=False)  # only files this command drew itself
            field = Specialist._meta.get_field("photo")
            stale = field.generate_filename(person, f"demo-portrait-{person.pk}.png")
            if field.storage.exists(stale):
                field.storage.delete(stale)  # a leftover drawn earlier; keeps one file per person
            person.photo.save(f"demo-portrait-{person.pk}.png", ContentFile(data), save=False)
            Specialist.objects.filter(pk=person.pk).update(photo=person.photo.name)
            self.stdout.write(f"drew: #{person.pk} {person.name}")
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Done: {len(targets)} portrait(s)."))
