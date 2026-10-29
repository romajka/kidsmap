"""Versioned private working copies; no live content writes on autosave."""
from django.core.exceptions import FieldDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from catalog.models import ServerDraft
from catalog.services import publication


class DraftConflict(Exception):
    def __init__(self, draft=None): self.draft = draft


ALLOWED_CREATE = {'place'}
PLACE_EDITOR_DRAFT_FIELDS = {'region', 'moderation_note', 'photo-clear', 'cover_photo-clear',
                             'delete_gallery_ids', 'gallery_order', 'gallery_captions', '_editor_base_signature', '_draft_media_selection'}


def editor_base_signature(target):
    """Content and candidate versions are distinct optimistic concurrency guards."""
    import hashlib
    import json
    from catalog.models import VolunteerPlaceRevision
    revision = VolunteerPlaceRevision.objects.filter(place=target).values_list('pk', 'version', 'status').first() if target and target.pk else None
    return hashlib.sha256(json.dumps([target.pk if target else None,
        target.content_version if target else 0, revision], separators=(',', ':')).encode()).hexdigest()


def _check_editor_base(fields, target, draft=None):
    signature = fields.get('_editor_base_signature')
    if signature is not None and signature != editor_base_signature(target):
        raise DraftConflict(draft)


def _number(value):
    if type(value) is not int or value < 0: raise ValidationError('Invalid version.')
    return value


def _actor(user):
    return publication.fresh_actor(user)


def _target(user, kind, target_id):
    if kind not in publication.TARGETS: raise ValidationError('Invalid target type.')
    if target_id is None:
        if kind not in ALLOWED_CREATE: raise ValidationError('Unsupported create target.')
        from catalog.services.staff_roles import can_use_volunteer_workspace
        if can_use_volunteer_workspace(user): return None
        from catalog.services.owner_place_use_cases import ensure_owner_permission
        if not ensure_owner_permission(user=user).ok: raise PermissionDenied
        return None
    if type(target_id) is not int or target_id < 1: raise ValidationError('Invalid target ID.')
    target = publication.locked_target(kind, target_id)
    publication.authorize(user, target, kind)
    return target


def _fields(kind, fields):
    allowed = publication.fields_for(kind) - {'photo','cover_photo','gallery'}
    if kind == 'place':
        allowed |= PLACE_EDITOR_DRAFT_FIELDS
    if not isinstance(fields, dict) or len(str(fields)) > 65536 or not set(fields) <= allowed:
        raise ValidationError('Unknown or oversized fields.')
    for name, value in fields.items():
        if name == '_draft_media_selection':
            fields[name] = _manifest_items(value)
            continue
        if value is None: continue
        if name == '_editor_base_signature':
            import re
            if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
                raise ValidationError('Invalid editor base signature.')
            continue
        if name in {'photo-clear', 'cover_photo-clear'}:
            if type(value) is not bool: raise ValidationError('Invalid photo selection.')
            continue
        if name == 'gallery_captions':
            import re
            from catalog.models import PlacePhoto
            limit = PlacePhoto._meta.get_field('caption').max_length
            if not isinstance(value, dict) or len(value) > 10 or any(
                not isinstance(key, str) or not re.fullmatch(r'(?:saved:[1-9][0-9]{0,18}|candidate:[a-f0-9]{64}|new:[0-9])', key)
                or not isinstance(caption, str) or len(caption) > limit for key, caption in value.items()):
                raise ValidationError('Invalid gallery captions.')
            continue
        if name in {'delete_gallery_ids', 'gallery_order'}:
            import json
            import re
            if isinstance(value, str):
                try: value = json.loads(value)
                except (ValueError, TypeError): raise ValidationError('Invalid gallery selection.')
            pattern = r'(?:[1-9][0-9]{0,18}|candidate:[a-f0-9]{64})' if name == 'delete_gallery_ids' else r'(?:saved:[1-9][0-9]{0,18}|candidate:[a-f0-9]{64}|new:[0-9])'
            if not isinstance(value, list) or len(value) > 10 or any(not isinstance(key, str) or not re.fullmatch(pattern, key) for key in value) or len(set(value)) != len(value):
                raise ValidationError('Invalid gallery selection.')
            fields[name] = value
            continue
        if isinstance(value, (dict, list)):
            if name not in {'pricing_plans', 'nested_pricing', 'structured_schedule', 'gallery', 'public_links'}: raise ValidationError({name: ['Invalid field type.']})
        elif not isinstance(value, (str, int, float, bool)):
            raise ValidationError({name: ['Invalid field type.']})
        if name in {'pricing_plans', 'nested_pricing', 'structured_schedule', 'public_links'} or value == '': continue
        try: field = publication.TARGETS[kind]._meta.get_field(name)
        except FieldDoesNotExist: continue  # Form-only controls are checked by the final form.
        try:
            converted = field.to_python(value)
            if not field.is_relation:
                field.run_validators(converted)
        except ValidationError as exc:
            raise ValidationError({name: exc.messages}) from exc
        if field.is_relation:
            if not field.remote_field.model.objects.filter(pk=converted).exists():
                raise ValidationError({name: ['Unknown relation.']})
    return fields


def serialize(draft, *, include_fields=True, media_url_name="server_draft_media_file"):
    result = {'draft_id': str(draft.pk), 'schema_version': draft.schema_version, 'version': draft.version,
              'source_version': draft.source_version, 'target_type': draft.target_type, 'target_id': draft.target_id,
              'saved_at': draft.saved_at.isoformat(), 'status': 'server_saved', 'errors': {},
              'photo_saved': bool(draft.photo_name), 'materialized_place_id': draft.materialized_place_id}
    result['media_manifest'] = public_media_manifest(draft, url_name=media_url_name)
    result['photo_saved'] = result['photo_saved'] or any(row['role'] == 'main' for row in result['media_manifest'])
    if include_fields: result['fields'] = draft.fields
    return result


@transaction.atomic
def save(*, user, data):
    user = _actor(user)
    kind = data['target_type']; target_id = data.get('target_id')
    schema = _number(data['schema_version']); expected = _number(data['expected_version'])
    if schema != publication.SCHEMA_VERSION: raise DraftConflict()
    fields = _fields(kind, data['fields'])
    draft_id = data.get('draft_id')
    if draft_id is None:
        if expected != 0: raise DraftConflict()
        target = _target(user, kind, target_id)
        _check_editor_base(fields, target)
        source = _number(data.get('source_version', 0))
        if source != (target.content_version if target else 0): raise DraftConflict()
        return ServerDraft.objects.create(actor=user, target_type=kind, target_id=target_id,
            schema_version=schema, source_version=source, fields=fields)
    from uuid import UUID
    try: draft_id = UUID(str(draft_id))
    except (ValueError, TypeError): raise ValidationError('Invalid draft ID.')
    target = _target(user, kind, target_id)
    _check_editor_base(fields, target)
    draft = ServerDraft.objects.select_for_update().filter(pk=draft_id).first()
    if draft is None:
        if expected != 0: raise ServerDraft.DoesNotExist
        source = _number(data.get('source_version', 0))
        if source != (target.content_version if target else 0): raise DraftConflict()
        draft, created = ServerDraft.objects.get_or_create(pk=draft_id, defaults={
            'actor': user, 'target_type': kind, 'target_id': target_id,
            'schema_version': schema, 'source_version': source, 'fields': fields})
        if created: return draft
        # A simultaneous retry may win the insert; it must match byte-for-byte.
        if draft.actor_id != user.pk or draft.target_type != kind or draft.target_id != target_id: raise PermissionDenied
        if draft.schema_version != schema or draft.source_version != source or draft.version != 1 or draft.fields != fields:
            raise DraftConflict(draft)
        return draft
    if draft.actor_id != user.pk: raise PermissionDenied
    if draft.target_type != kind or draft.target_id != target_id: raise PermissionDenied
    if draft.materialized_place_id: raise DraftConflict(draft)
    _check_editor_base(draft.fields, target, draft)
    if draft.schema_version != schema or draft.source_version != (target.content_version if target else 0): raise DraftConflict(draft)
    if 'source_version' in data and _number(data['source_version']) != draft.source_version: raise DraftConflict(draft)
    # A response can be lost after commit. Only the immediately preceding,
    # byte-equivalent field state may retry without another version increment.
    if expected == draft.version - 1 and draft.fields == fields: return draft
    if expected != draft.version: raise DraftConflict(draft)
    draft.fields = fields; draft.version += 1; draft.save(update_fields=['fields', 'version', 'saved_at'])
    return draft


@transaction.atomic
def read(*, user, draft_id):
    user = _actor(user)
    draft = ServerDraft.objects.filter(pk=draft_id).first()
    if draft is None: raise ServerDraft.DoesNotExist
    if draft.actor_id != user.pk: raise PermissionDenied
    target = _target(user, draft.target_type, draft.target_id)
    if draft.materialized_place_id:
        _target(user, 'place', draft.materialized_place_id)
    elif target and draft.source_version != target.content_version:
        raise DraftConflict(draft)
    if not draft.materialized_place_id:
        _check_editor_base(draft.fields, target, draft)
    return draft


class PrivateDraftStorage(FileSystemStorage):
    def url(self, name):
        raise ValueError('Private drafts are available only through an authorized reader')


def private_storage():
    """Store outside MEDIA_ROOT, which nginx serves without Django auth."""
    from pathlib import Path
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured
    media = Path(settings.MEDIA_ROOT).resolve()
    configured = getattr(settings, 'PRIVATE_DRAFT_MEDIA_ROOT', None)
    root = Path(configured or (media.parent / ('private_' + media.name + '_drafts'))).resolve()
    if root == media or root.is_relative_to(media):
        raise ImproperlyConfigured('Private drafts must be outside MEDIA_ROOT')
    return PrivateDraftStorage(location=root, base_url=None,
        file_permissions_mode=0o600, directory_permissions_mode=0o700)


def public_media_manifest(draft, *, url_name="server_draft_media_file"):
    """Expose only opaque identifiers and authorized routes, never storage paths."""
    from django.urls import reverse
    return [{'id': row['id'], 'role': row['role'], 'order': row['order'],
             'name': row['name'], 'size': row['size'],
             **({key: row[key] for key in ('desired_role', 'desired_order')}
                if row['role'] == 'pending' and 'desired_role' in row and 'desired_order' in row else {}),
             'url': reverse(url_name, args=[draft.pk, row['id']])}
            for row in (draft.media_manifest or []) if row.get('role') != 'deleted']


def _media_uuid(value):
    from uuid import UUID
    try: return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError): raise ValidationError('Invalid media ID.')


def _media_draft(user, draft_id, *, write=False):
    """Lock target before draft, matching text autosave and publication ordering."""
    user = _actor(user)
    probe = read(user=user, draft_id=draft_id)
    draft = ServerDraft.objects.select_for_update().get(pk=probe.pk) if write else probe
    if write and draft.materialized_place_id: raise DraftConflict(draft)
    if draft.target_type != 'place': raise ValidationError('Media target unsupported.')
    return draft


@transaction.atomic
def upload_media(*, user, draft_id, expected_version, media_id, file, desired_role=None, desired_order=None):
    """Stage one immutable image. UUID/content retry is safe after a lost response."""
    import hashlib
    from catalog.services.image_uploads import normalize_uploaded_image, MAX_IMAGE_BATCH_BYTES, MAX_IMAGE_SOURCE_BYTES
    draft = _media_draft(user, draft_id, write=True)
    expected = _number(expected_version)
    identifier = _media_uuid(media_id)
    desired = {}
    if desired_role is not None or desired_order is not None:
        if desired_role not in {'main', 'cover', 'gallery'} or type(desired_order) is not int or not 0 <= desired_order < (10 if desired_role == 'gallery' else 1):
            raise ValidationError('Invalid desired image role or order.')
        desired = {'desired_role': desired_role, 'desired_order': desired_order}
    if not file or not 0 < file.size <= MAX_IMAGE_SOURCE_BYTES:
        raise ValidationError('Invalid image size.')
    digest = hashlib.sha256()
    for chunk in file.chunks(): digest.update(chunk)
    signature = digest.hexdigest()
    file.seek(0)
    rows = list(draft.media_manifest or [])
    existing = next((row for row in rows if row['id'] == identifier), None)
    if existing:
        if not 1 <= expected <= draft.version: raise DraftConflict(draft)
        if existing.get('role') == 'deleted' or existing.get('digest') != signature:
            raise DraftConflict(draft)
        if existing.get('role') == 'pending' and desired and any(existing.get(key) != value for key, value in desired.items()):
            raise DraftConflict(draft)
        return draft
    if expected != draft.version: raise DraftConflict(draft)
    # Permit one replacement batch alongside the last committed manifest.
    active = [row for row in rows if row.get('role') != 'deleted']
    if len(rows) >= 512 or len(active) >= 24 or sum(row.get('role') == 'pending' for row in active) >= 12:
        raise ValidationError('Too many draft images.')
    normalized = normalize_uploaded_image(file)
    if sum(row['size'] for row in active) + normalized.size > 2 * MAX_IMAGE_BATCH_BYTES:
        raise ValidationError('Draft image batch too large.')
    storage = private_storage()
    name = storage.save(f'drafts/{draft.pk}/{identifier}.webp', normalized)
    rows.append({'id': identifier, 'role': 'pending', 'order': 0, 'path': name,
                 'name': normalized.name, 'size': normalized.size, 'digest': signature, **desired})
    try:
        draft.media_manifest = rows
        draft.version += 1
        draft.save(update_fields=['media_manifest', 'version', 'saved_at'])
    except BaseException:
        storage.delete(name)
        raise
    return draft


def _manifest_items(items):
    from catalog.services.image_uploads import MAX_GALLERY_IMAGES
    if not isinstance(items, list) or len(items) > MAX_GALLERY_IMAGES + 2:
        raise ValidationError('Invalid manifest.')
    result = []
    identifiers = set()
    positions = {'main': [], 'cover': [], 'gallery': []}
    for item in items:
        if not isinstance(item, dict) or set(item) != {'id', 'role', 'order'}:
            raise ValidationError('Invalid manifest item.')
        identifier = _media_uuid(item['id'])
        role, order = item['role'], item['order']
        if not isinstance(role, str) or role not in positions or type(order) is not int or order < 0 or identifier in identifiers:
            raise ValidationError('Invalid image role or order.')
        identifiers.add(identifier)
        positions[role].append(order)
        result.append({'id': identifier, 'role': role, 'order': order})
    for role, orders in positions.items():
        if len(orders) > (MAX_GALLERY_IMAGES if role == 'gallery' else 1) or sorted(orders) != list(range(len(orders))):
            raise ValidationError('Invalid image order.')
    return sorted(result, key=lambda row: ({'main': 0, 'cover': 1, 'gallery': 2}[row['role']], row['order']))


@transaction.atomic
def save_media_manifest(*, user, draft_id, expected_version, items):
    """Commit roles/order and remove omitted files only after the database commits."""
    from catalog.services.image_uploads import MAX_IMAGE_BATCH_BYTES
    draft = _media_draft(user, draft_id, write=True)
    expected = _number(expected_version)
    items = _manifest_items(items)
    rows = list(draft.media_manifest or [])
    current = [{key: row[key] for key in ('id', 'role', 'order')}
               for row in rows if row.get('role') != 'deleted']
    if expected != draft.version:
        if 1 <= expected < draft.version and current == items: return draft
        raise DraftConflict(draft)
    available = {row['id']: row for row in rows if row.get('role') != 'deleted'}
    if any(item['id'] not in available for item in items):
        raise ValidationError('Unknown image ID.')
    selected = [{**available[item['id']], **item} for item in items]
    if sum(row['size'] for row in selected) > MAX_IMAGE_BATCH_BYTES:
        raise ValidationError('Image batch too large.')
    if current == items: return draft
    selected_ids = {row['id'] for row in selected}
    removed = [row for row in rows if row['id'] not in selected_ids]
    # Tombstones stop delayed uploads from resurrecting a removed UUID.
    tombstones = [{'id': row['id'], 'role': 'deleted', 'digest': row.get('digest', '')} for row in removed]
    draft.media_manifest = selected + tombstones
    draft.version += 1
    draft.save(update_fields=['media_manifest', 'version', 'saved_at'])
    paths = [row['path'] for row in removed if row.get('path')]
    if paths:
        storage = private_storage()
        transaction.on_commit(lambda: [storage.delete(path) for path in paths])
    return draft


@transaction.atomic
def open_media(*, user, draft_id, media_id):
    draft = _media_draft(user, draft_id)
    identifier = _media_uuid(media_id)
    row = next((row for row in (draft.media_manifest or [])
                if row['id'] == identifier and row.get('role') != 'deleted'), None)
    if row is None: raise FileNotFoundError
    return private_storage().open(row['path'], 'rb'), row['name']


@transaction.atomic
def upload_photo(*, user, draft_id, expected_version, file):
    from uuid import uuid4
    from catalog.services.image_uploads import normalize_uploaded_image
    user = _actor(user)
    probe = ServerDraft.objects.filter(pk=draft_id, actor=user).first()
    if probe is None:
        if ServerDraft.objects.filter(pk=draft_id).exists(): raise PermissionDenied
        raise ServerDraft.DoesNotExist
    target = _target(user, probe.target_type, probe.target_id)
    if target and probe.source_version != target.content_version: raise DraftConflict(probe)
    draft = ServerDraft.objects.select_for_update().filter(pk=draft_id).first()
    if draft is None: raise ServerDraft.DoesNotExist
    if draft.actor_id != user.pk: raise PermissionDenied
    if draft.materialized_place_id: raise DraftConflict(draft)
    if (draft.target_type, draft.target_id) != (probe.target_type, probe.target_id): raise DraftConflict(draft)
    if draft.target_type != 'place': raise ValidationError('Photo target unsupported.')
    if _number(expected_version) != draft.version: raise DraftConflict(draft)
    if not file: raise ValidationError('Photo required.')
    normalized = normalize_uploaded_image(file)
    storage = private_storage()
    name = storage.save(f'drafts/{draft.pk}/{uuid4().hex}.webp', normalized)
    previous = draft.photo_name
    try:
        draft.photo_name = name; draft.version += 1
        draft.save(update_fields=['photo_name','version','saved_at'])
    except BaseException:
        storage.delete(name)
        raise
    if previous: transaction.on_commit(lambda: storage.delete(previous))
    return draft


@transaction.atomic
def materialize_place(*, user, draft_id, expected_version, request):
    """Create once from a complete draft; never publish automatically."""
    from django.http import QueryDict
    from catalog.controllers.owner_places_controller import OwnerPlacesController
    user = _actor(user)
    draft = ServerDraft.objects.select_for_update().filter(pk=draft_id).first()
    if draft is None: raise ServerDraft.DoesNotExist
    if draft.actor_id != user.pk: raise PermissionDenied
    if draft.target_type != 'place' or draft.target_id is not None: raise ValidationError('Only new Place drafts may materialize.')
    if draft.materialized_place_id:
        _target(user, 'place', draft.materialized_place_id)
        return draft, {}
    if _number(expected_version) != draft.version: raise DraftConflict(draft)
    if not any(isinstance(draft.fields.get(name), str) and draft.fields[name].strip() for name in ('name_az','name_ru','name_en')):
        return draft, {'name_az':['Name required before creating a Place.']}
    if not draft.fields.get('category'):
        return draft, {'category':['Category required before creating a Place.']}
    data = QueryDict(mutable=True)
    for name,value in draft.fields.items():
        data[name] = json_value(value)
    data['form_action']='save_draft'
    data['server_draft_id']=str(draft.pk)
    # Private draft media stays private; publication media promotion needs an explicit later action.
    result=OwnerPlacesController.build_default().create_place(request=request,data=data,files={},draft_save_only=True)
    if not result.ok:
        errors={name:[str(message) for message in messages] for name,messages in result.form.errors.items()} if result.form else {'__all__':[str(result.message)]}
        return draft, errors
    draft.materialized_place=result.place
    draft.save(update_fields=['materialized_place','saved_at'])
    return draft, {}


@transaction.atomic
def discard(*, user, draft_id, expected_version):
    """Discard only an actor's unmaterialized working copy, including stale work."""
    user = _actor(user)
    probe = ServerDraft.objects.filter(pk=draft_id, actor=user).first()
    if probe is None:
        if ServerDraft.objects.filter(pk=draft_id).exists(): raise PermissionDenied
        raise ServerDraft.DoesNotExist
    _target(user, probe.target_type, probe.target_id)
    draft = ServerDraft.objects.select_for_update().get(pk=probe.pk, actor=user)
    if draft.materialized_place_id or _number(expected_version) != draft.version:
        raise DraftConflict(draft)
    paths = {row['path'] for row in (draft.media_manifest or []) if row.get('path')}
    if draft.photo_name: paths.add(draft.photo_name)
    draft.delete()
    if paths:
        storage = private_storage()
        transaction.on_commit(lambda: [storage.delete(path) for path in paths])


def json_value(value):
    import json
    return json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else str(value)


@transaction.atomic
def mark_explicit_save(*, user, draft_id, place, target_id, cutoff=None, expected_version=None):
    """Retain data, but stop older same-actor working copies resuming after save."""
    from uuid import UUID
    from django.utils import timezone
    user = _actor(user)
    if target_id is not None and target_id != place.pk:
        return False
    target = _target(user, 'place', place.pk)  # Target lock precedes draft locks.
    cutoff = cutoff or timezone.now()
    copies = ServerDraft.objects.select_for_update().filter(actor=user,
        target_type='place', target_id=target_id).order_by('pk')
    matched = None
    if draft_id:
        try: identifier = UUID(str(draft_id))
        except (ValueError, TypeError): return False
        matched = next((row for row in copies if row.pk == identifier), None)
        if matched is None or (matched.materialized_place_id and matched.materialized_place_id != place.pk):
            return False
        if expected_version is not None:
            try: version = int(expected_version)
            except (ValueError, TypeError): return False
            if version != matched.version or matched.saved_at > cutoff: return False
    if target_id is None:
        if matched is None: return False
        matched.materialized_place = target
        matched.save(update_fields=['materialized_place', 'saved_at'])
        return True
    retired = False
    for draft in copies:
        if draft.materialized_place_id or draft.saved_at > cutoff or draft.source_version > target.content_version:
            continue
        if draft.schema_version != publication.SCHEMA_VERSION:
            continue
        draft.materialized_place = target
        draft.save(update_fields=['materialized_place', 'saved_at'])
        retired = True
    return retired
