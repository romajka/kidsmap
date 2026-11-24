"""Poster facts for afisha surfaces: shape, focus point and dominant colour.

Facts are computed once at upload (or by ``backfill_event_image_meta``) and
stored on the row, so rendering never decodes an image.
"""
from __future__ import annotations

import logging
import re

from PIL import Image, ImageOps, UnidentifiedImageError

from .image_uploads import MAX_IMAGE_SOURCE_BYTES, MAX_IMAGE_SOURCE_DIMENSION, MAX_IMAGE_SOURCE_PIXELS

logger = logging.getLogger(__name__)

PORTRAIT, LANDSCAPE, SQUARE = 'portrait', 'landscape', 'square'
ORIENTATION_CHOICES = ((PORTRAIT, 'Portrait'), (LANDSCAPE, 'Landscape'), (SQUARE, 'Square'))
DEFAULT_FOCUS = 50
HEX = re.compile(r'^#[0-9a-f]{6}$')


def orientation_for(width, height) -> str:
    """portrait below 0.85 w/h, landscape above 1.2, square in between."""
    if not width or not height or width <= 0 or height <= 0:
        return ''
    ratio = width / height
    if ratio < 0.85:
        return PORTRAIT
    if ratio > 1.2:
        return LANDSCAPE
    return SQUARE


# A frame follows the photo's own shape between these bounds (9:16 … 2:1);
# only photos beyond them get the blurred fill around the whole picture.
FRAME_MIN_RATIO = 9 / 16
FRAME_MAX_RATIO = 2.0


def frame_ratio(width, height) -> str:
    """CSS aspect-ratio for a frame around this photo, e.g. '1.4356'; '' if unknown.

    A plain string with a dot so templates never localise it into '1,4356'."""
    if not width or not height or width <= 0 or height <= 0:
        return ''
    ratio = min(FRAME_MAX_RATIO, max(FRAME_MIN_RATIO, width / height))
    return f'{ratio:.4f}'


def clamp_focus(value, default=DEFAULT_FOCUS) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, number))


def dominant_color(image: Image.Image) -> str:
    """Average colour weighted by saturation, so white margins do not win."""
    with image.convert('RGB') as rgb:
        small = rgb.resize((24, 24), Image.Resampling.BILINEAR)
    total = r_sum = g_sum = b_sum = 0
    for r, g, b in small.getdata():
        weight = max(r, g, b) - min(r, g, b) + 1
        total += weight
        r_sum += r * weight
        g_sum += g * weight
        b_sum += b * weight
    small.close()
    if not total:
        return ''
    return '#{:02x}{:02x}{:02x}'.format(round(r_sum / total), round(g_sum / total), round(b_sum / total))


def analyze(file_field) -> dict:
    """width/height/orientation/dominant_color of a stored image, or {} if unreadable."""
    if not file_field or not getattr(file_field, 'name', ''):
        return {}
    try:
        storage = file_field.storage
        if not storage.exists(file_field.name) or storage.size(file_field.name) > MAX_IMAGE_SOURCE_BYTES:
            return {}
        with storage.open(file_field.name, 'rb') as handle, Image.open(handle) as decoded:
            if (decoded.width * decoded.height > MAX_IMAGE_SOURCE_PIXELS
                    or max(decoded.size) > MAX_IMAGE_SOURCE_DIMENSION):
                return {}
            width, height = decoded.size
            if decoded.getexif().get(0x0112) in (5, 6, 7, 8):  # rotated by EXIF
                width, height = height, width
            decoded.draft('RGB', (256, 256))  # cheap JPEG downscale; colour only
            with ImageOps.exif_transpose(decoded) as oriented:
                color = dominant_color(oriented)
        return {'width': width, 'height': height, 'orientation': orientation_for(width, height),
                'dominant_color': color}
    except (OSError, ValueError, TypeError, AttributeError, NotImplementedError,
            UnidentifiedImageError, Image.DecompressionBombError) as exc:
        logger.warning('Event image analysis skipped (%s)', type(exc).__name__)
        return {}


def _meta(source, *, prefix):
    get = lambda name: getattr(source, prefix + name, None)  # noqa: E731
    width, height = get('width'), get('height')
    orientation = get('orientation') or orientation_for(width, height)
    color = get('dominant_color') or ''
    return {
        'width': width, 'height': height,
        'orientation': orientation or PORTRAIT,  # unknown posters are shown whole
        'ratio': frame_ratio(width, height),
        'fx': clamp_focus(get('focus_x')), 'fy': clamp_focus(get('focus_y')),
        'color': color if HEX.match(color) else '',
    }


def _urls(file_field):
    from .responsive_images import responsive_image
    data = responsive_image(file_field)
    return {'src': data['src'], 'srcset': data['srcset'], 'thumb': data['preview'], 'original': file_field.url}


def poster(event) -> dict | None:
    """Main poster of an event for cards and the hero; None without a photo."""
    photo = getattr(event, 'photo', None)
    if not photo or not getattr(photo, 'name', ''):
        return None
    try:
        urls = _urls(photo)
    except (ValueError, OSError):
        return None
    data = {**_meta(event, prefix='photo_'), **urls}
    data['shown_whole'] = data['orientation'] != LANDSCAPE
    return data


def gallery(event) -> list[dict]:
    """Extra photos in their saved order, with captions parsed for credits."""
    from catalog.templatetags.event_editorial import event_caption
    items = []
    photos = event.gallery.all
    for photo in (photos() if callable(photos) else photos):
        image = getattr(photo, 'image', None)
        if not image:
            continue
        try:
            if getattr(image, 'name', ''):
                urls = _urls(image)
            else:  # already-resolved URL (previews, tests)
                urls = {'src': image.url, 'srcset': '', 'thumb': image.url, 'original': image.url}
        except (ValueError, OSError):
            continue
        items.append({'id': getattr(photo, 'pk', None), 'caption': event_caption(getattr(photo, 'caption', '') or ''),
                      **_meta(photo, prefix=''), **urls})
    return items


# --- persistence -----------------------------------------------------------
FIELD_MAP = {
    # model label: (file field, prefix of the fact fields)
    'catalog.event': ('photo', 'photo_'),
    'catalog.eventphoto': ('image', ''),
}


def _spec(instance):
    return FIELD_MAP.get(instance._meta.label_lower)


def remember_source(instance):
    """Called on load: lets a save tell whether the file was replaced."""
    spec = _spec(instance)
    if spec:
        if spec[0] not in instance.__dict__:  # deferred field: unknown, not "replaced"
            instance._km_image_source = None
            return
        field = instance.__dict__[spec[0]]
        instance._km_image_source = getattr(field, 'name', field) or ''


def refresh_meta(instance, *, force=False, variants=True) -> bool:
    """Store size/orientation/colour for a new or replaced file. Returns True if written."""
    spec = _spec(instance)
    if not spec or not instance.pk:
        return False
    field_name, prefix = spec
    image = getattr(instance, field_name)
    name = getattr(image, 'name', '') or ''
    source = getattr(instance, '_km_image_source', None)
    replaced = source is not None and source != name
    missing = getattr(instance, prefix + 'width') is None
    if not name:
        updates = {prefix + 'width': None, prefix + 'height': None, prefix + 'orientation': '', prefix + 'dominant_color': ''}
        changed = any(getattr(instance, key) != value for key, value in updates.items())
    elif force or replaced or missing:
        facts = analyze(image)
        if not facts:
            return False
        updates = {prefix + key: value for key, value in facts.items()}
        changed = True
        if variants:
            from .responsive_images import generate_variants
            generate_variants(image)
    else:
        return False
    instance._km_image_source = name
    if not changed:
        return False
    type(instance)._base_manager.filter(pk=instance.pk).update(**updates)
    for key, value in updates.items():
        setattr(instance, key, value)
    return True


# --- forms -------------------------------------------------------------------
def prepare_focus_fields(form, names=('photo_focus_x', 'photo_focus_y')):
    """Focus inputs are optional: old clients and API callers simply omit them."""
    from django import forms as django_forms
    for name in names:
        field = form.fields.get(name)
        if field is None:
            continue
        field.required = False
        field.widget = django_forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 1, 'inputmode': 'numeric', 'class': 'field km-focus__number'})


def clean_focus_fields(form, cleaned, names=('photo_focus_x', 'photo_focus_y')):
    """An empty focus keeps the stored value (or the centre); range is validated by the model."""
    for name in names:
        if name in form.fields and cleaned.get(name) is None:
            cleaned[name] = getattr(form.instance, name, None)
            if cleaned[name] is None:
                cleaned[name] = DEFAULT_FOCUS
    return cleaned
