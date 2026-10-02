"""Versioned private working copies; no live content writes on autosave."""
from django.core.exceptions import FieldDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from catalog.models import ServerDraft
from catalog.services import publication


class DraftConflict(Exception):
    def __init__(self, draft=None): self.draft = draft


ALLOWED_CREATE = {'place'}
PLACE_EDITOR_DRAFT_FIELDS = {'region', 'moderation_note'}


def _number(value):
    if type(value) is not int or value < 0: raise ValidationError('Invalid version.')
    return value


def _actor(user):
    return publication.fresh_actor(user)


def _target(user, kind, target_id):
    if kind not in publication.TARGETS: raise ValidationError('Invalid target type.')
    if target_id is None:
        if kind not in ALLOWED_CREATE: raise ValidationError('Unsupported create target.')
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
        if value is None: continue
        if isinstance(value, (dict, list)):
            if name not in {'pricing_plans', 'nested_pricing', 'structured_schedule', 'gallery'}: raise ValidationError({name: ['Invalid field type.']})
        elif not isinstance(value, (str, int, float, bool)):
            raise ValidationError({name: ['Invalid field type.']})
        if name in {'pricing_plans', 'nested_pricing', 'structured_schedule'} or value == '': continue
        try: field = publication.TARGETS[kind]._meta.get_field(name)
        except FieldDoesNotExist: continue  # Form-only controls are checked by the final form.
        converted = field.to_python(value)
        if field.is_relation:
            if not field.remote_field.model.objects.filter(pk=converted).exists():
                raise ValidationError({name: ['Unknown relation.']})
        else: field.run_validators(converted)
    return fields


def serialize(draft, *, include_fields=True):
    result = {'draft_id': str(draft.pk), 'schema_version': draft.schema_version, 'version': draft.version,
              'source_version': draft.source_version, 'target_type': draft.target_type, 'target_id': draft.target_id,
              'saved_at': draft.saved_at.isoformat(), 'status': 'server_saved', 'errors': {},
              'photo_saved': bool(draft.photo_name), 'materialized_place_id': draft.materialized_place_id}
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
        source = _number(data.get('source_version', 0))
        if source != (target.content_version if target else 0): raise DraftConflict()
        return ServerDraft.objects.create(actor=user, target_type=kind, target_id=target_id,
            schema_version=schema, source_version=source, fields=fields)
    from uuid import UUID
    try: draft_id = UUID(str(draft_id))
    except (ValueError, TypeError): raise ValidationError('Invalid draft ID.')
    draft = ServerDraft.objects.select_for_update().filter(pk=draft_id).first()
    if draft is None:
        if expected != 0: raise ServerDraft.DoesNotExist
        target = _target(user, kind, target_id)
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
    target = _target(user, kind, target_id)
    if draft.schema_version != schema or draft.source_version != (target.content_version if target else 0): raise DraftConflict(draft)
    if 'source_version' in data and _number(data['source_version']) != draft.source_version: raise DraftConflict(draft)
    if expected == 0 and draft.version == 1 and draft.fields == fields: return draft
    if expected != draft.version: raise DraftConflict(draft)
    draft.fields = fields; draft.version += 1; draft.save(update_fields=['fields', 'version', 'saved_at'])
    return draft


@transaction.atomic
def read(*, user, draft_id):
    user = _actor(user)
    draft = ServerDraft.objects.filter(pk=draft_id).first()
    if draft is None: raise ServerDraft.DoesNotExist
    if draft.actor_id != user.pk: raise PermissionDenied
    _target(user, draft.target_type, draft.target_id)
    return draft


def private_storage():
    """Store outside MEDIA_ROOT, which nginx serves without Django auth."""
    from pathlib import Path
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    media = Path(settings.MEDIA_ROOT)
    return FileSystemStorage(location=media.parent / ('private_' + media.name + '_drafts'), base_url=None)


@transaction.atomic
def upload_photo(*, user, draft_id, expected_version, file):
    from uuid import uuid4
    from catalog.services.image_uploads import normalize_uploaded_image
    user = _actor(user)
    draft = ServerDraft.objects.select_for_update().filter(pk=draft_id).first()
    if draft is None: raise ServerDraft.DoesNotExist
    if draft.actor_id != user.pk: raise PermissionDenied
    _target(user, draft.target_type, draft.target_id)
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
    # Private draft media stays private; publication media promotion needs an explicit later action.
    result=OwnerPlacesController.build_default().create_place(request=request,data=data,files={},draft_save_only=True)
    if not result.ok:
        errors={name:[str(message) for message in messages] for name,messages in result.form.errors.items()} if result.form else {'__all__':[str(result.message)]}
        return draft, errors
    draft.materialized_place=result.place
    draft.save(update_fields=['materialized_place','saved_at'])
    return draft, {}


def json_value(value):
    import json
    return json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else str(value)


@transaction.atomic
def mark_explicit_save(*, user, draft_id, place, target_id):
    """Keep a saved working copy out of future resume choices after explicit save."""
    if not draft_id:
        return False
    from uuid import UUID
    try:
        identifier = UUID(str(draft_id))
    except (ValueError, TypeError):
        return False
    draft = ServerDraft.objects.select_for_update().filter(pk=identifier, actor=user,
        target_type='place', target_id=target_id).first()
    if draft is None or (draft.materialized_place_id and draft.materialized_place_id != place.pk):
        return False
    _target(user, 'place', place.pk)
    draft.materialized_place = place
    draft.save(update_fields=['materialized_place', 'saved_at'])
    return True
