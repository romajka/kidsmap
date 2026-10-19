"""Normalize uploaded SVG icons to a bounded, passive vector vocabulary."""
import math
import re
from xml.etree import ElementTree

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'
SHAPES = frozenset({'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'})
TAGS = SHAPES | {'svg', 'g', 'defs', 'clipPath', 'linearGradient', 'radialGradient',
                 'stop', 'use', 'title', 'desc'}
IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_.:-]*\Z')
NUMBER_TEXT = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
NUMBER = re.compile(NUMBER_TEXT)
NUMBERS = re.compile(rf'\s*{NUMBER_TEXT}(?:[\s,]+{NUMBER_TEXT})*\s*\Z')
LENGTH = re.compile(rf'({NUMBER_TEXT})(%|px)?\Z')
LOCAL_PAINT = re.compile(r'''url\(\s*(?:"\#([^"\s]+)"|'\#([^'\s]+)'|\#([^\s)]+))\s*\)\Z''')
GEOMETRY = {'width', 'height', 'x', 'y', 'cx', 'cy', 'r', 'rx', 'ry', 'x1', 'y1',
            'x2', 'y2', 'fx', 'fy', 'fr', 'offset', 'pathLength'}
PRESENTATION = {'fill', 'stroke', 'color', 'stop-color', 'fill-opacity', 'stroke-opacity',
                'opacity', 'stop-opacity', 'stroke-width', 'stroke-dashoffset',
                'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin',
                'stroke-miterlimit', 'fill-rule', 'clip-rule', 'vector-effect',
                'visibility', 'display', 'clip-path'}
ENUMS = {
    'stroke-linecap': {'butt', 'round', 'square', 'inherit'},
    'stroke-linejoin': {'miter', 'miter-clip', 'round', 'bevel', 'arcs', 'inherit'},
    'fill-rule': {'nonzero', 'evenodd', 'inherit'},
    'clip-rule': {'nonzero', 'evenodd', 'inherit'},
    'vector-effect': {'none', 'non-scaling-stroke'},
    'visibility': {'visible', 'hidden', 'collapse', 'inherit'},
    'display': {'inline', 'none', 'inherit'},
    'gradientUnits': {'userSpaceOnUse', 'objectBoundingBox'},
    'clipPathUnits': {'userSpaceOnUse', 'objectBoundingBox'},
    'spreadMethod': {'pad', 'reflect', 'repeat'},
    'version': {'1.0', '1.1', '2.0'},
    'role': {'img', 'presentation', 'none'},
}


def _numbers(value):
    if not NUMBERS.fullmatch(value):
        raise ValueError('Invalid SVG numbers')
    values = NUMBER.findall(value)
    if len(values) > 4096 or any(not math.isfinite(float(v)) or abs(float(v)) > 10_000_000 for v in values):
        raise ValueError('SVG numeric limit')
    return [float(v) for v in values]


def _length(value):
    match = LENGTH.fullmatch(value)
    if not match:
        raise ValueError('Invalid SVG length')
    _numbers(match[1])


def _transform(value):
    remaining = value.strip()
    count = 0
    while remaining:
        match = re.match(r'(matrix|translate|scale|rotate|skewX|skewY)\(([^()]*)\)', remaining)
        if not match or count >= 32:
            raise ValueError('Invalid SVG transform')
        numbers = _numbers(match[2])
        allowed = {'matrix': {6}, 'translate': {1, 2}, 'scale': {1, 2},
                   'rotate': {1, 3}, 'skewX': {1}, 'skewY': {1}}
        if len(numbers) not in allowed[match[1]]:
            raise ValueError('Invalid SVG transform arity')
        remaining = remaining[match.end():].lstrip(' ,\t\r\n')
        count += 1


def _attribute(key, value, tag, owners, references):
    value = value.strip()
    if key == 'id':
        if not IDENTIFIER.fullmatch(value):
            raise ValueError('Invalid SVG identifier')
    elif key == 'viewBox':
        box = _numbers(value)
        if tag != 'svg' or len(box) != 4 or box[2] <= 0 or box[2] != box[3]:
            raise ValueError('Square SVG viewBox required')
    elif key in {'fill', 'stroke', 'color', 'stop-color', 'clip-path'}:
        local = LOCAL_PAINT.fullmatch(value)
        if local:
            target = next(v for v in local.groups() if v is not None)
            if not IDENTIFIER.fullmatch(target):
                raise ValueError('Invalid SVG reference')
            references.append((owners, 'clip' if key == 'clip-path' else 'paint', target))
            return f'url(#{target})'
        if key == 'clip-path':
            if value != 'none':
                raise ValueError('Local SVG clip reference required')
        elif not (re.fullmatch(r'#[0-9a-fA-F]{3,8}', value)
                  or re.fullmatch(r'[A-Za-z]+', value)
                  or re.fullmatch(r'(?:rgb|rgba|hsl|hsla)\([0-9\s.,%+/-]+\)', value)):
            raise ValueError('Invalid SVG color')
    elif key == 'href':
        if tag != 'use' or not value.startswith('#') or not IDENTIFIER.fullmatch(value[1:]):
            raise ValueError('Local SVG shape reference required')
        references.append((owners, 'use', value[1:]))
    elif key in GEOMETRY or key in {'stroke-width', 'stroke-dashoffset', 'stroke-miterlimit',
                                    'fill-opacity', 'stroke-opacity', 'opacity', 'stop-opacity'}:
        _length(value)
    elif key == 'stroke-dasharray':
        if value != 'none':
            for length in re.split(r'[\s,]+', value):
                _length(length)
    elif key in {'transform', 'gradientTransform'}:
        _transform(value)
    elif key == 'd':
        if tag != 'path' or not re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAaEe0-9+.,\s-]*', value):
            raise ValueError('Invalid SVG path')
        if NUMBER.findall(value):
            _numbers(' '.join(NUMBER.findall(value)))
    elif key == 'points':
        if tag not in {'polyline', 'polygon'} or len(_numbers(value)) % 2:
            raise ValueError('Invalid SVG points')
    elif key in ENUMS:
        if value not in ENUMS[key]:
            raise ValueError('Invalid SVG presentation value')
    elif key == 'preserveAspectRatio':
        if not re.fullmatch(r'none|x(?:Min|Mid|Max)Y(?:Min|Mid|Max)(?: (?:meet|slice))?', value):
            raise ValueError('Invalid SVG aspect ratio')
    elif key in {'class', 'aria-labelledby'}:
        if not value or any(not IDENTIFIER.fullmatch(v) for v in value.split()):
            raise ValueError('Invalid SVG identifier list')
    elif key == 'aria-label':
        if len(value) > 500:
            raise ValueError('SVG label too long')
    else:
        raise ValueError('Unsupported SVG attribute')
    return value


def sanitize_svg_icon(source):
    """Return canonical UTF-8 SVG; reject unsupported structure before storage."""
    if len(source) > 500 * 1024:
        raise ValueError('SVG byte limit')
    text = source.decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('SVG document declarations are not supported')
    root = ElementTree.fromstring(text)
    identifiers, references = {}, []
    stack = [(root, 1, ())]
    count = 0
    while stack:
        node, depth, ancestors = stack.pop()
        count += 1
        if count > 2048 or depth > 32:
            raise ValueError('SVG structure limit')
        tag = node.tag.removeprefix('{'+SVG_NS+'}')
        if tag not in TAGS or (depth == 1 and tag != 'svg') or (depth > 1 and tag == 'svg'):
            raise ValueError('Unsupported SVG element')
        if tag in {'title', 'desc', 'stop'} and len(node):
            raise ValueError('Unsupported SVG children')
        if tag in SHAPES | {'use'} and any(child.tag.removeprefix('{'+SVG_NS+'}') not in {'title', 'desc'} for child in node):
            raise ValueError('SVG shapes only support descriptive children')
        node.tag = '{'+SVG_NS+'}'+tag
        attrs = dict(node.attrib)
        identifier = attrs.get('id')
        owners = ancestors + ((identifier,) if identifier else ())
        if identifier:
            if identifier in identifiers:
                raise ValueError('Duplicate SVG identifier')
            identifiers[identifier] = tag
        style = attrs.pop('style', '')
        for declaration in style.split(';'):
            if not declaration.strip():
                continue
            key, separator, value = declaration.partition(':')
            if not separator or key.strip() not in PRESENTATION:
                raise ValueError('Unsupported SVG style')
            attrs[key.strip()] = value.strip()
        node.attrib.clear()
        for key, value in attrs.items():
            if key == '{'+XLINK_NS+'}href':
                key = 'href'
            node.set(key, _attribute(key, value, tag, owners, references))
        if depth == 1 and 'viewBox' not in node.attrib:
            raise ValueError('SVG viewBox required')
        stack.extend((child, depth+1, owners) for child in node)
    edges = {key: set() for key in identifiers}
    for owners, kind, target in references:
        allowed = SHAPES if kind == 'use' else {'clipPath'} if kind == 'clip' else {'linearGradient', 'radialGradient'}
        if identifiers.get(target) not in allowed:
            raise ValueError('Unsupported SVG reference target')
        for owner in owners:
            edges[owner].add(target)
    colors = {}
    for identifier in edges:
        pending = [(identifier, False)]
        while pending:
            item, leaving = pending.pop()
            if leaving:
                colors[item] = 2
            elif colors.get(item) == 1:
                raise ValueError('Cyclic SVG reference')
            elif colors.get(item) != 2:
                colors[item] = 1
                pending.append((item, True))
                pending.extend((child, False) for child in edges[item])
    ElementTree.register_namespace('', SVG_NS)
    result = ElementTree.tostring(root, encoding='utf-8')
    if len(result) > 500 * 1024:
        raise ValueError('Normalized SVG byte limit')
    return result
