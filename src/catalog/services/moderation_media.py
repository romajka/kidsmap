"""Read-only image presentation, called only after moderation detail authorization."""
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from django.core.exceptions import SuspiciousFileOperation
from catalog.models import Place,PlacePhoto

RASTER_SUFFIXES=frozenset({'.jpg','.jpeg','.png','.webp','.gif','.avif','.bmp','.heic','.heif','.tif','.tiff'})

def _image(name,storage,caption=''):
    item={'url':'','caption':caption if isinstance(caption,str) else ''}
    if not isinstance(name,str) or not name:return item
    path=PurePosixPath(name)
    if (name!=path.as_posix() or path.is_absolute() or len(path.parts)<2 or path.parts[0]!='places'
        or '..' in path.parts or any(c in name for c in ('\\','%',':','?','#'))
        or path.suffix.lower() not in RASTER_SUFFIXES):return item
    try:
        if not storage.exists(name):return item
        url=storage.url(name);parts=urlsplit(url)
        if (parts.scheme not in ('','http','https') or parts.username or parts.password
            or (not parts.scheme and (not url.startswith('/') or url.startswith('//')))):
            return item
    except (OSError,ValueError,NotImplementedError,SuspiciousFileOperation):return item
    return {**item,'url':url}


def _images(value,field):
    if field!='gallery':
        if value in (None,''):return []
        return [_image(value,Place._meta.get_field(field).storage)]
    if value in (None,[]):return []
    if not isinstance(value,list) or len(value)>10:return [{'url':'','caption':''}]
    entries=[]
    for index,item in enumerate(value):
        if not isinstance(item,dict):entries.append((index,{'url':'','caption':''}));continue
        order=item.get('order',0)
        if isinstance(order,bool) or not isinstance(order,int) or order<0:order=index
        entries.append((order,_image(item.get('image'),PlacePhoto._meta.get_field('image').storage,item.get('caption',''))))
    return [image for _,image in sorted(entries,key=lambda entry:entry[0])]


def comparison_rows(row):
    """Keep text/affiliation behavior; only known Place image fields get URLs."""
    from django.utils.translation import gettext as _
    keys=row['revision'].changed_fields if row['kind']=='place' else []
    result=[]
    for index,(label,before,after) in enumerate(row['changes']):
        key=keys[index] if index<len(keys) else ''
        media=key in {'photo','cover_photo','gallery'}
        result.append({'label':_('Галерея') if key=='gallery' else label,'before':before,'after':after,
            'media':media,'before_images':_images(before,key) if media else [],
            'after_images':_images(after,key) if media else []})
    return result
