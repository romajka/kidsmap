"""Bounded public map pages; the catalog owns visibility and offer matching."""
import math
from django.core.exceptions import ValidationError
from django.db.models import Case, F, FloatField, Q, When
from catalog.services.map_payload import serialize_map_places

PAGE_SIZE = 100


def request_window(params):
    """Only finite complete bounds and a nonnegative bigint keyset cursor."""
    cursor=params.get('after','')
    if cursor:
        if not cursor.isascii() or not cursor.isdigit() or len(cursor)>19 or int(cursor)>9223372036854775807:
            raise ValidationError('Invalid map cursor.')
        cursor=int(cursor)
    else:
        cursor=0
    names=('south','west','north','east')
    present=[name in params for name in names]
    if not any(present):return cursor,None
    if not all(present):raise ValidationError('Complete map bounds required.')
    try:bounds={name:float(params[name]) for name in names}
    except (TypeError,ValueError,OverflowError):raise ValidationError('Invalid map bounds.')
    if not all(math.isfinite(v) for v in bounds.values()) or not (-90<=bounds['south']<=bounds['north']<=90) or not (-180<=bounds['west']<=180 and -180<=bounds['east']<=180):
        raise ValidationError('Invalid map bounds.')
    return cursor,bounds


def coordinate_queryset(queryset, bounds=None):
    """Match map_identity: authoritative address-only venues have no map pin."""
    confirmed=Q(confirmed_location__isnull=False,venue_confirmed_at__isnull=False,
        confirmed_location__confirmed_at__isnull=False,confirmed_location__archived_at__isnull=True)
    qs=queryset.alias(
        km_map_lat=Case(When(confirmed,then=F('confirmed_location__lat')),default=F('lat'),output_field=FloatField()),
        km_map_lng=Case(When(confirmed,then=F('confirmed_location__lng')),default=F('lng'),output_field=FloatField()),
    ).filter(km_map_lat__gte=-90,km_map_lat__lte=90,km_map_lng__gte=-180,km_map_lng__lte=180)
    qs=qs.exclude(km_map_lat__gt=-.001,km_map_lat__lt=.001,km_map_lng__gt=-.001,km_map_lng__lt=.001)
    if bounds:
        qs=qs.filter(km_map_lat__gte=bounds['south'],km_map_lat__lte=bounds['north'])
        if bounds['west']<=bounds['east']:
            qs=qs.filter(km_map_lng__gte=bounds['west'],km_map_lng__lte=bounds['east'])
        else:
            qs=qs.filter(Q(km_map_lng__gte=bounds['west'])|Q(km_map_lng__lte=bounds['east']))
    return qs


def build_map_page(queryset, language_code, filters=None, *, after=0, bounds=None, newest_first=False):
    qs=coordinate_queryset(queryset,bounds)
    total=qs.count()
    # The homepage must select recent records before paging, not just reorder
    # the oldest page after serialization. Keep legacy ascending cursors valid.
    ordering = '-pk' if newest_first else 'pk'
    window = qs.filter(pk__lt=after) if newest_first and after else qs
    if not newest_first:
        window = window.filter(pk__gt=after)
    ids=list(window.order_by(ordering).values_list('pk',flat=True)[:PAGE_SIZE+1])
    has_more=len(ids)>PAGE_SIZE
    selected=ids[:PAGE_SIZE]
    points=serialize_map_places(qs.filter(pk__in=selected).order_by(ordering),language_code,filters,
        ordering=(ordering,) if newest_first else None) if selected else []
    return {'points':points,'count':total,'has_more':has_more,'next_cursor':selected[-1] if has_more else None}


def page_metadata(page):
    return {key:page[key] for key in ('count','has_more','next_cursor')}
