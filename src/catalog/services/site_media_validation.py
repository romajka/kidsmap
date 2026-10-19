"""Admin site media boundary; preserves accepted bytes, including transparent art."""
import math
import re
import warnings
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

_INVALID = _('Загрузите корректный JPG, PNG или WebP. SVG разрешён только для логотипа и партнёров.')
_BIG = _('Файл слишком большой. Максимум: %(limit)s КБ.')
_DIMENSIONS = _('Изображение слишком большое: максимум 12000 пикселей по стороне и 50 мегапикселей.')
_SVG = _('SVG должен быть статичным и не содержать скриптов, внешних ресурсов или встроенных изображений.')
_SVG_NS = 'http://www.w3.org/2000/svg'
_SVG_TAGS = frozenset(('svg', 'g', 'defs', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
                       'polygon', 'linearGradient', 'radialGradient', 'stop', 'clipPath', 'title', 'desc'))
_SVG_ATTRS = frozenset(('id', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
                       'width', 'height', 'viewBox', 'preserveAspectRatio', 'd', 'points', 'transform',
                       'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-width', 'stroke-opacity',
                       'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray',
                       'stroke-dashoffset', 'opacity', 'clip-path', 'clip-rule', 'clipPathUnits',
                       'gradientUnits', 'gradientTransform', 'spreadMethod', 'offset', 'stop-color',
                       'stop-opacity', 'fx', 'fy', 'fr', 'role', 'aria-label', 'aria-hidden',
                       'vector-effect', 'color'))
_FORMATS = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
_MIMES = {'JPEG': {'image/jpeg', 'image/jpg'}, 'PNG': {'image/png'}, 'WEBP': {'image/webp'},
          'SVG': {'image/svg+xml'}}


def _check_dimensions(width, height):
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        raise ValidationError(_INVALID, code='invalid_site_media')
    if max(width, height) > 12000 or width * height > 50_000_000:
        raise ValidationError(_DIMENSIONS, code='site_media_dimensions')


def _validate_static_svg(raw):
    try:
        text = raw.decode('utf-8-sig')
        document = text
        declaration = re.match(r'^\s*<\?xml\s+[^?]*\?>', text)
        if declaration:
            encoding = re.search(r'encoding\s*=\s*[\'"]([^\'"]+)', declaration[0], re.I)
            if encoding and encoding[1].lower() != 'utf-8':
                raise ValueError('encoding')
            text = text[declaration.end():]
        # Block DTD/entities and processing instructions before the XML parser.
        if re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b|<\?', text, re.I) or '\x00' in text:
            raise ValueError('declaration')
        root = ElementTree.fromstring(document)
        if root.tag != '{' + _SVG_NS + '}svg':
            raise ValueError('root')
        stack = [(root, 1)]
        count = 0
        while stack:
            element, depth = stack.pop()
            count += 1
            if count > 20_000 or depth > 64 or not element.tag.startswith('{' + _SVG_NS + '}'):
                raise ValueError('complexity or namespace')
            if element.tag.split('}', 1)[1] not in _SVG_TAGS:
                raise ValueError('element')
            for key, value in element.attrib.items():
                if key == '{http://www.w3.org/XML/1998/namespace}space' and value in {'preserve', 'default'}:
                    continue
                if key not in _SVG_ATTRS or len(value) > 65536:
                    raise ValueError('attribute')
                without_fragments = re.sub(r'url\(\s*#[A-Za-z_][A-Za-z0-9_.:-]*\s*\)', '', value, flags=re.I)
                if re.search(r'url\s*\(|javascript:|data:|://|[\\@]', without_fragments, re.I):
                    raise ValueError('external value')
            stack.extend((child, depth + 1) for child in element)
        width = float(root.get('width', '300').removesuffix('px'))
        height = float(root.get('height', '150').removesuffix('px'))
        _check_dimensions(width, height)
        if 'viewBox' in root.attrib:
            box = [float(x) for x in re.split(r'[\s,]+', root.attrib['viewBox'].strip())]
            if len(box) != 4 or not all(math.isfinite(x) for x in box):
                raise ValueError('viewBox')
            _check_dimensions(box[2], box[3])
    except ValidationError:
        raise
    except (UnicodeError, ElementTree.ParseError, ValueError, TypeError):
        raise ValidationError(_SVG, code='unsafe_site_svg') from None


def validate_site_media_upload(uploaded_file, *, field=None, placement=None):
    """Validate one NEW upload before any ORM/storage mutation; rewind on all paths.

    500KiB for logo/partners, 2MiB otherwise; no resize, recolor or byte rewriting.
    SVG permits only a restrictive static UTF-8 drawing subset for logo/partners.
    """
    small = field == 'logo' or placement == 'HOME_PARTNERS'
    limit = (500 if small else 2048) * 1024
    try:
        if uploaded_file.size > limit:
            raise ValidationError(_BIG, params={'limit': limit // 1024}, code='site_media_size')
        uploaded_file.seek(0)
        raw = uploaded_file.read(limit + 1)
        if len(raw) > limit:
            raise ValidationError(_BIG, params={'limit': limit // 1024}, code='site_media_size')
        if not raw:
            raise ValidationError(_INVALID, code='invalid_site_media')
        suffix = Path(uploaded_file.name or '').suffix.lower()
        mime = (uploaded_file.content_type or '').lower().strip()
        expected = 'SVG' if suffix == '.svg' else _FORMATS.get(suffix)
        if not expected or (mime not in {'', 'application/octet-stream'} and mime not in _MIMES[expected]):
            raise ValidationError(_INVALID, code='invalid_site_media')
        if expected == 'SVG':
            if not small:
                raise ValidationError(_INVALID, code='invalid_site_media')
            _validate_static_svg(raw)
        else:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(BytesIO(raw), formats=['JPEG', 'PNG', 'WEBP']) as probe:
                        if probe.format != expected or getattr(probe, 'n_frames', 1) != 1:
                            raise ValidationError(_INVALID, code='invalid_site_media')
                        _check_dimensions(*probe.size)
                        probe.verify()
                    with Image.open(BytesIO(raw), formats=['JPEG', 'PNG', 'WEBP']) as decoded:
                        decoded.load()
            except ValidationError:
                raise
            except (Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise ValidationError(_DIMENSIONS, code='site_media_dimensions') from None
            except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
                raise ValidationError(_INVALID, code='invalid_site_media') from None
        return uploaded_file
    finally:
        uploaded_file.seek(0)
