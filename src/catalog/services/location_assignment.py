"""Server-owned assignment policy. Geometry itself has no Place dependency."""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.services.district_geometry import resolve_location
from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP, normalize_to_key

LOCATION_FIELDS = {'lat', 'lng', 'district', 'city', 'location_resolution_status', 'location_dataset_version'}
UNRESOLVED_MESSAGE = _('Не удалось определить район. Проверьте точку или сохраните черновик для проверки администратором.')


def can_override_location(actor):
    from catalog.services.staff_roles import is_volunteer
    return bool(actor and actor.is_active and actor.is_staff and not is_volunteer(actor)
                and actor.has_perm('catalog.override_place_location'))


def set_location_override(place, *, actor, city, district, reason):
    """Stage an authorized exception; save() persists it atomically with Place."""
    city, district, reason = normalize_to_key(city), normalize_to_key(district), str(reason or '').strip()
    if not can_override_location(actor):
        raise ValidationError(_('Нет права на ручное исправление географии.'))
    if not reason or len(reason) > 1000:
        raise ValidationError(_('Укажите причину ручного исправления (до 1000 символов).'))
    if city not in AZERBAIJAN_REGIONS_MAP or (city == 'baku' and district not in BAKU_DISTRICTS_MAP) or (city != 'baku' and district not in ('', city)):
        raise ValidationError(_('Город и район не согласованы.'))
    result = resolve_location(place.lat, place.lng)
    if result.status == 'invalid_coordinates':
        raise ValidationError(_('Для ручного исправления укажите корректные координаты.'))
    place._location_override_request = dict(actor=actor, city=city, district=district or city,
        reason=reason, lat=float(place.lat), lng=float(place.lng))


def _current_override(place, result):
    if not place.pk:
        return None
    return place.location_overrides.filter(is_current=True, lat=place.lat, lng=place.lng,
        dataset_version=result.dataset_version).first()


def prepare_place_location(place, *, previous, update_fields, using):
    """Called inside Place.save's row lock. Returns changed fields and audit data."""
    fields = None if update_fields is None else set(update_fields)
    if previous and fields is not None and not fields & (LOCATION_FIELDS | {'status', 'is_active'}):
        return set(), None
    # A partial write must resolve the coordinates that actually reach the DB.
    if previous and fields is not None:
        for name in ('lat', 'lng', 'district', 'city', 'status', 'is_active'):
            if name not in fields:
                setattr(place, name, getattr(previous, name))
    moved = previous is None or (place.lat, place.lng) != (previous.lat, previous.lng)
    manual_changed = previous is None or (place.city, place.district) != (previous.city, previous.district)
    publishing = previous is not None and place.status == 'published' and place.is_active and not (previous.status == 'published' and previous.is_active)
    requested = getattr(place, '_location_override_request', None)
    if previous and not moved and not manual_changed and not publishing and not requested and previous.location_resolution_status != 'overridden':
        # Do not rewrite legacy geography when unrelated content is edited.
        return set(), None
    result = resolve_location(place.lat, place.lng)
    audit = None
    override = _current_override(place, result) if not moved else None
    if requested:
        if (requested['lat'], requested['lng']) != (place.lat, place.lng):
            raise ValidationError(_('Координаты изменились. Подтвердите ручное исправление заново.'))
        set_location_override(place, **{key: requested[key] for key in ('actor', 'city', 'district', 'reason')})
        place.city, place.district = requested['city'], requested['district']
        place.location_resolution_status = 'overridden'
        audit = dict(changed_by=requested['actor'], reason=requested['reason'], lat=place.lat, lng=place.lng,
                     city=place.city, district=place.district, automatic_city=result.city_key,
                     automatic_district=result.district_key, automatic_status=result.status,
                     dataset_version=result.dataset_version)
    elif override:
        place.city, place.district = override.city, override.district
        place.location_resolution_status = 'overridden'
    else:
        # Compatibility for old integrations creating an unlocated record. Forms
        # enforce draft/publication readiness; no fabricated city is assigned.
        if previous is None and place.lat is None and place.lng is None:
            place.city = ''
            place.location_resolution_status = 'legacy'
            return {'city', 'location_resolution_status'}, None
        if result.status != 'resolved' and place.status == 'published' and place.is_active:
            raise ValidationError({'district': UNRESOLVED_MESSAGE})
        place.city, place.district = result.city_key, result.district_key
        place.location_resolution_status = result.status
    place.location_dataset_version = result.dataset_version
    if previous and (moved or audit or not override):
        place.location_overrides.using(using).filter(is_current=True).update(is_current=False)
    return {'city', 'district', 'location_resolution_status', 'location_dataset_version'}, audit


def clean_place_location(form, cleaned):
    """Return True when handled. Event forms retain their separate contract."""
    if getattr(getattr(form, '_meta', None), 'model', None) is None or form._meta.model._meta.concrete_model._meta.model_name != 'place':
        return False
    place = form.instance
    lat, lng = cleaned.get('lat'), cleaned.get('lng')
    if 'lat' not in form.fields or 'lng' not in form.fields:
        return False
    previous_point = (place.lat, place.lng)
    moved = not place.pk or (lat, lng) != previous_point
    old_district = normalize_to_key(place.district)
    region = normalize_to_key(cleaned.get('region', ''))
    district = normalize_to_key(cleaned.get('district', ''))
    result = resolve_location(lat, lng)
    form.location_resolution = result
    draft = bool(getattr(form, 'draft_save_only', False) or getattr(form, 'geocoding_check_only', False)
                 or getattr(form, 'coordinate_refresh_only', False))
    if 'status' in form.fields and cleaned.get('status', place.status) != 'published':
        draft = True
    if hasattr(form, 'submit_for_moderation') and place.pk and not form.submit_for_moderation:
        draft = draft or not (place.status == 'published' and place.is_active)
    if not getattr(form, 'require_location_region', True) and not getattr(form, 'location_publication_required', False):
        # A volunteer proposal is not publication; moderation rechecks it.
        draft = True
    old_region = 'baku' if old_district.startswith('baku_') else old_district
    unchanged = bool(place.pk and not moved and district in ('', old_district) and region in ('', old_region))
    # An explicit resubmission/publication never receives legacy compatibility.
    publishing = bool(form.data and '_publish_place' in form.data) or bool(getattr(form, 'submit_for_moderation', False)) or bool(getattr(form, 'location_publication_required', False))
    was_live = place.pk and place.status == 'published' and place.is_active
    if unchanged and was_live and not publishing and place.location_resolution_status == 'legacy':
        cleaned['district'] = old_district
        return True
    reason = str(cleaned.get('location_override_reason') or '').strip()
    if reason:
        # Forms know the actor only through admin.get_form, never POST.
        old_lat, old_lng = place.lat, place.lng
        place.lat, place.lng = lat, lng
        try:
            set_location_override(place, actor=getattr(form, 'location_actor', None), city=region,
                                  district=district, reason=reason)
            cleaned['district'] = district if region == 'baku' else region
            place.city = region
        except ValidationError as exc:
            form.add_error('location_override_reason' if 'location_override_reason' in form.fields else None, exc)
        finally:
            place.lat, place.lng = old_lat, old_lng
        return True
    override = _current_override(place, result) if not moved else None
    if override and unchanged:
        cleaned['district'] = override.district
        return True
    if result.status == 'resolved':
        # A stale value submitted with a moved pin is auto-replaced. An explicit
        # conflicting manual choice is an error, even in drafts.
        expired_override = place.location_resolution_status == 'overridden' and place.location_dataset_version != result.dataset_version
        stale = bool(place.pk and (moved or expired_override) and district == old_district and region in ('', old_region))
        if not stale:
            if region and region != result.city_key:
                form.add_error('region', _('Город не соответствует выбранной точке на карте.'))
            if district and district != result.district_key:
                form.add_error('district', _('Район не соответствует выбранной точке на карте.'))
        cleaned['region'], cleaned['district'] = result.city_key, result.district_key
    else:
        cleaned['region'], cleaned['district'] = result.city_key, ''
        place.district = ''  # Readiness must not fall back to the stored stale district.
        if not draft:
            form.add_error('district', UNRESOLVED_MESSAGE)
        if (lat is not None or lng is not None) and result.status == 'invalid_coordinates':
            form.add_error('lat', _('Укажите корректные широту и долготу.'))
    # Non-form metadata is never accepted from client input.
    place.city = result.city_key
    place.location_resolution_status = result.status
    place.location_dataset_version = result.dataset_version
    return True
