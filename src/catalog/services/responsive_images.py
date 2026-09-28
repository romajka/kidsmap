"""Pre-generated photo sizes. Rendering never decodes or writes an image."""
from __future__ import annotations

import hashlib
import json
import logging
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from PIL import Image, ImageOps, UnidentifiedImageError

from .image_uploads import MAX_IMAGE_SOURCE_BYTES, MAX_IMAGE_SOURCE_DIMENSION, MAX_IMAGE_SOURCE_PIXELS

WIDTHS = (320, 640, 960, 1280)
logger = logging.getLogger(__name__)


def _directory(image):
    # A replacement at the same source path gets new, immutable derivative URLs.
    stamp = image.storage.get_modified_time(image.name).isoformat()
    size = image.storage.size(image.name)
    revision = hashlib.sha256(f'v1:{image.name}:{stamp}:{size}'.encode()).hexdigest()[:32]
    return f'responsive-images/v1/{revision}'


@lru_cache(maxsize=2048)
def _read_manifest(storage, name):
    with storage.open(name, 'rb') as f:
        data = json.load(f)
    parent = name.rsplit('/', 1)[0]
    if not isinstance(data, dict) or not isinstance(data.get('variants'), list) or not data['variants']:
        raise ValueError('Invalid image manifest')
    if not all(isinstance(data.get(k), int) and data[k] > 0 for k in ('width', 'height')):
        raise ValueError('Invalid image dimensions')
    for item in data['variants']:
        if not isinstance(item.get('width'), int) or item['width'] <= 0:
            raise ValueError('Invalid variant width')
        if not isinstance(item.get('name'), str) or item['name'].rsplit('/', 1)[0] != parent:
            raise ValueError('Invalid variant path')
    return data


def responsive_image(image, *, target_storage=None):
    """Return ready URLs or an original-only fallback, without generating files."""
    result = {'src': '', 'srcset': '', 'preview': '', 'width': None, 'height': None}
    if not image or not getattr(image, 'name', ''):
        return result
    storage = target_storage if target_storage is not None else image.storage
    try:
        result['src'] = result['preview'] = image.url
        manifest = f'{_directory(image)}/manifest.json'
        # Do not cache misses: a generation command in another process can
        # publish files while an existing Gunicorn worker keeps serving pages.
        if not storage.exists(manifest):
            return result
        data = _read_manifest(storage, manifest)
        variants = data['variants']
        if not all(storage.exists(item['name']) for item in variants):
            return result
        urls = [(storage.url(item['name']), item['width']) for item in variants]
        result.update(
            src=next((url for url, width in urls if width >= 640), urls[-1][0]),
            preview=urls[0][0],
            srcset=', '.join(f'{url} {width}w' for url, width in urls),
            width=data['width'], height=data['height'],
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError, NotImplementedError):
        pass
    return result


def generate_variants(image, *, target_storage=None):
    """Write bounded WebP derivatives, retaining the source byte-for-byte."""
    existing = responsive_image(image, target_storage=target_storage)
    if existing['srcset']:
        return {**existing, 'generated': False}
    if not image or not getattr(image, 'name', ''):
        return {**existing, 'generated': False}
    storage = target_storage if target_storage is not None else image.storage
    try:
        if not image.storage.exists(image.name):
            return {**existing, 'generated': False}
        directory = _directory(image)
        if image.storage.size(image.name) > MAX_IMAGE_SOURCE_BYTES:
            return {**existing, 'generated': False}
        with image.storage.open(image.name, 'rb') as f, Image.open(f) as decoded:
            if (getattr(decoded, 'is_animated', False)
                    or decoded.width * decoded.height > MAX_IMAGE_SOURCE_PIXELS
                    or max(decoded.size) > MAX_IMAGE_SOURCE_DIMENSION):
                return {**existing, 'generated': False}
            with ImageOps.exif_transpose(decoded) as oriented:
                width, height = oriented.size
                variants = []
                for target_width in sorted({min(w, width) for w in WIDTHS}):
                    name = f'{directory}/{target_width}.webp'
                    if not storage.exists(name):
                        with oriented.convert('RGBA' if oriented.mode in ('RGBA', 'LA') or 'transparency' in oriented.info else 'RGB') as resized:
                            resized.thumbnail((target_width, max(1, round(height * target_width / width))), Image.Resampling.LANCZOS)
                            # Keep the advertised width equal to the encoded width.
                            target_width = resized.width
                            output = BytesIO()
                            resized.save(output, format='WEBP', quality=80, method=4)
                        name = storage.save(name, ContentFile(output.getvalue()))
                    variants.append({'name': name, 'width': target_width})
                manifest = f'{directory}/manifest.json'
                # Only derivative metadata can be replaced; never delete source files.
                if storage.exists(manifest):
                    storage.delete(manifest)
                storage.save(manifest, ContentFile(json.dumps({'width': width, 'height': height, 'variants': variants}).encode()))
                _read_manifest.cache_clear()
        return {**responsive_image(image, target_storage=target_storage), 'generated': True}
    except (OSError, ValueError, TypeError, AttributeError, NotImplementedError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        logger.warning('Responsive image generation skipped (%s)', type(exc).__name__)
        return {**existing, 'generated': False}


def static_photo(path):
    """Use static source photos with the shared media derivative destination."""
    found = finders.find(path)
    if not found:
        return None
    source = FileSystemStorage(location=Path(found).parents[len(Path(path).parts) - 1])
    from django.templatetags.static import static
    return SimpleNamespace(name=path, storage=source, url=static(path))


def responsive_static_image(path):
    return responsive_image(static_photo(path), target_storage=default_storage)
