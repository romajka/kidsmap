"""Read-only saved content for the admin list; public Place fields stay intact."""
import copy

from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, CharField, F, Q, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from catalog.models import Place, PlacePhoto, VolunteerPlaceRevision

ACTIVE_REVISIONS = ('draft', 'pending', 'rejected')


def _editable_revision_ids(request, model_admin):
    if request is None or not model_admin.has_change_permission(request):
        return ()
    cache = getattr(request, '_km_list_revision_ids', None)
    if cache is not None:
        return cache
    from catalog.services.business_team import platform_has_action
    from catalog.services.publication import authorize
    platform_editor = platform_has_action(user=request.user, action='place.publish')
    allowed = []
    for revision in VolunteerPlaceRevision.objects.filter(
            status__in=ACTIVE_REVISIONS, place__isnull=False).select_related('place'):
        place = revision.place
        if not model_admin.has_change_permission(request, place):
            continue
        if not platform_editor:
            try:
                authorize(request.user, place, 'place')
            except PermissionDenied:
                continue
        allowed.append(place.pk)
    request._km_list_revision_ids = tuple(allowed)
    return request._km_list_revision_ids


def _publication_ids(request, model_admin):
    if request is None or not model_admin.has_change_permission(request):
        return ()
    cached = getattr(request, '_km_list_publication_ids', None)
    if cached is not None:
        return cached
    from catalog.services.business_team import platform_has_action
    allowed = ()
    if platform_has_action(user=request.user, action='place.publish'):
        allowed = tuple(place.pk for place in Place.objects.only('pk').iterator()
                        if model_admin.has_change_permission(request, place))
    request._km_list_publication_ids = allowed
    return allowed


def with_saved_location(queryset, request, model_admin):
    """One effective-coordinate predicate shared by list filters and counts.

    A missing JSON key inherits live data; an explicit null/empty clears it.
    Text casts preserve zero and avoid interpreting JSON null as a coordinate.
    """
    eligible = Q(pk__in=_editable_revision_ids(request, model_admin),
                 volunteer_revision__status__in=ACTIVE_REVISIONS)
    queryset = queryset.annotate(km_list_publish_allowed=Case(
        When(pk__in=_publication_ids(request, model_admin), then=Value(True)),
        default=Value(False), output_field=BooleanField()))
    queryset = queryset.annotate(km_saved_candidate_allowed=Case(
        When(eligible, then=Value(True)), default=Value(False), output_field=BooleanField()))
    queryset = queryset.alias(**{
        f'km_list_{name}': Case(
            When(eligible & Q(**{'volunteer_revision__payload__has_key': name}),
                 then=KeyTextTransform(name, F('volunteer_revision__payload'))),
            default=Cast(F(name), CharField()), output_field=CharField())
        for name in ('lat', 'lng')
    })
    missing = (Q(km_list_lat__isnull=True) | Q(km_list_lat='') |
               Q(km_list_lng__isnull=True) | Q(km_list_lng=''))
    return queryset.annotate(km_saved_has_coordinates=Case(
        When(missing, then=Value(False)), default=Value(True), output_field=BooleanField()))


def saved_presentation(place):
    """Project only list content on a copy after queryset permission checks."""
    if not getattr(place, 'km_saved_candidate_allowed', False):
        return place
    revision = getattr(place, 'volunteer_revision', None)
    if revision is None or revision.status not in ACTIVE_REVISIONS:
        return place
    candidate = copy.copy(place)
    candidate._state = copy.copy(place._state)
    candidate._public_file_exists_cache = {}
    for name in ('name', 'name_az', 'name_ru', 'name_en', 'address', 'lat', 'lng', 'photo', 'cover_photo'):
        if name in revision.payload:
            value = revision.payload[name]
            # Empty coordinate input is an explicit removal, just like JSON null.
            if name in ('lat', 'lng') and value == '':
                value = None
            setattr(candidate, name, Place._meta.get_field(name).to_python(value))
    return candidate


def saved_thumbnail_url(place):
    candidate = saved_presentation(place)
    if candidate.public_image_url:
        return candidate.public_image_url
    revision = getattr(place, 'volunteer_revision', None)
    if candidate is not place and 'gallery' in revision.payload:
        photos = [PlacePhoto(image=row['image'], order=row.get('order', 0))
                  for row in revision.payload['gallery'] if row.get('image')]
    else:
        photos = list(place.gallery.all())
    for photo in sorted(photos, key=lambda obj: (obj.order, obj.pk or 0)):
        if candidate._public_file_exists(photo.image):
            return photo.image.url
    return ''
