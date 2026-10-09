"""Proposed edits stay separate from live Place until atomic Superadmin review."""
import copy
import hashlib
import json

from django.core import signing
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision
from catalog.services.place_readiness import evaluate_form_readiness, publication_blocked_message
from catalog.services.place_schedule import serialize_place_schedule, dump_schedule_payload
from catalog.services.staff_roles import can_use_volunteer_workspace
from catalog.volunteer_forms import CONTENT_FIELDS, VolunteerPlaceForm
from catalog.services.place_duplicates import find_creator_duplicate
from catalog.services.permanent_place_rules import copy as t


def can_delete_working_place(place, revision=None):
    revision = revision if revision is not None else getattr(place, 'volunteer_revision', None)
    return (
        place.status in {Place.STATUS_DRAFT, Place.STATUS_REJECTED}
        and not place.is_active and not place.is_deleted and not place.owner_id
        and not place.is_temporary
        and (revision is None or revision.status in {'draft', 'rejected'})
    )


def json_value(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def content_snapshot(place):
    result = {}
    for name in CONTENT_FIELDS:
        field = Place._meta.get_field(name)
        value = getattr(place, field.attname)
        result[name] = str(value or "") if name in {"photo", "cover_photo"} else json_value(value)
    result["pricing_plans"] = json_value(place.pricing_plans)
    result["structured_schedule"] = serialize_place_schedule(place)
    return result


def live_snapshot(place):
    result = content_snapshot(place)
    for name in ("name", "slug", "slug_az", "slug_ru", "slug_en", "owner_id", "created_by_id", "is_active", "status", "is_verified", "deleted_at"):
        result[name] = json_value(getattr(place, name))
    return result


def base_token(place):
    digest = hashlib.sha256(json.dumps(live_snapshot(place), sort_keys=True).encode()).hexdigest()
    return signing.dumps({"place": place.pk, "digest": digest}, salt="volunteer-place")


def revision_base_matches(revision, place):
    if revision.dependencies:
        from catalog.services import publication
        current=publication.snapshot(place,'place')
        return (revision.schema_version == publication.SCHEMA_VERSION
                and revision.dependencies == publication.dependencies(place,'place')
                and all(current.get(k)==revision.base_snapshot.get(k) for k in revision.changed_fields))
    current = live_snapshot(place)
    # Older revisions never captured these RU fallback fields. Preserve the
    # current values when loading them; newly loaded forms still use a full
    # signed token, so subsequent edits cannot overwrite a concurrent change.
    for name in ("additional_info", "extra_conditions"):
        if name not in revision.base_snapshot:
            current.pop(name, None)
    return revision.base_snapshot == current


def token_matches(token, place):
    try:
        return signing.loads(token, salt="volunteer-place") == signing.loads(base_token(place), salt="volunteer-place")
    except signing.BadSignature:
        return False


def own_places(user):
    if not can_use_volunteer_workspace(user):
        raise PermissionDenied
    # A business-owner handover stops the volunteer from continuing to edit.
    return Place.objects.filter(created_by=user, owner__isnull=True, deleted_at__isnull=True, is_temporary=False)


def candidate_from_payload(place, payload):
    candidate = copy.copy(place)
    candidate._state = copy.copy(place._state)
    for name in (*CONTENT_FIELDS, 'nature', 'operating_state'):
        if name in payload:
            field = Place._meta.get_field(name)
            setattr(candidate, field.attname, field.to_python(payload[name]) if not field.is_relation else payload[name])
    candidate.pricing_plans = payload.get("pricing_plans", place.pricing_plans)
    candidate.pending_nested_pricing = payload.get("nested_pricing")
    return candidate


def editor_form(place, revision=None, *, data=None, files=None):
    payload = revision.payload if revision and revision.status != "approved" else content_snapshot(place)
    candidate = candidate_from_payload(place, payload)
    initial = {"base_token": base_token(place), "revision_version": revision.version if revision else 0}
    form = VolunteerPlaceForm(data, files, instance=candidate, initial=initial)
    if data is None:
        raw_schedule = dump_schedule_payload(payload.get("structured_schedule", serialize_place_schedule(place)))
        form.initial["structured_schedule"] = raw_schedule
        form.fields["structured_schedule"].initial = raw_schedule
        form.schedule_editor_payload = raw_schedule
        form.schedule_editor_days = payload.get("structured_schedule", [])
    return form


def _check_version(revision, version):
    if version != (revision.version if revision else 0):
        raise ValidationError(_("Данные уже изменились. Обновите страницу перед сохранением."))


def _working_place_queryset(user, source):
    if source == PlaceChangeAudit.SOURCE_VOLUNTEER:
        return own_places(user)
    if source == PlaceChangeAudit.SOURCE_ADMIN:
        if not (
            user.is_authenticated
            and user.is_active
            and user.is_staff
            and (user.is_superuser or user.has_perm("catalog.change_place"))
        ):
            raise PermissionDenied
        return Place.objects.filter(deleted_at__isnull=True, is_temporary=False)
    raise PermissionDenied


def _audit_working_changes(*, place, actor, source, old_snapshot, new_snapshot):
    entries = []
    for field_name in sorted(new_snapshot):
        old_value = old_snapshot.get(field_name)
        new_value = new_snapshot.get(field_name)
        if old_value == new_value:
            continue
        entries.append(PlaceChangeAudit(
            place=place,
            changed_by=actor,
            source=source,
            field_name=field_name,
            old_value=json.dumps(old_value, ensure_ascii=False, cls=DjangoJSONEncoder),
            new_value=json.dumps(new_value, ensure_ascii=False, cls=DjangoJSONEncoder),
        ))
    if entries:
        PlaceChangeAudit.objects.bulk_create(entries)


@transaction.atomic
def save_working_revision(*, user, place_id, data, files, source):
    places = _working_place_queryset(user, source)
    if source == PlaceChangeAudit.SOURCE_ADMIN and not place_id:
        raise PermissionDenied
    from catalog.services import publication
    place = publication.locked_target("place",place_id) if place_id else Place(created_by=user, status="draft", is_active=False)
    if place_id and not places.filter(pk=place.pk).exists():raise PermissionDenied
    revision = VolunteerPlaceRevision.objects.select_for_update().filter(place=place).first() if place.pk else None
    if source == PlaceChangeAudit.SOURCE_ADMIN and (
        revision is None or revision.status == VolunteerPlaceRevision.Status.APPROVED
    ):
        raise ValidationError(_("У места нет активной рабочей версии волонтёра."))

    form = editor_form(place, revision, data=data, files=files)
    if not form.is_valid():
        return place, revision, form
    try:
        action = data.get("action")
        allowed_actions = {"draft", "submit"} if source == PlaceChangeAudit.SOURCE_VOLUNTEER else {"admin_save"}
        if action not in allowed_actions:
            raise ValidationError(_("Недопустимое действие сохранения."))
        _check_version(revision, form.cleaned_data["revision_version"])
        if not token_matches(form.cleaned_data["base_token"], place):
            raise ValidationError(_("Карточка изменилась. Обновите страницу."))
        if revision and revision.status != "approved" and not revision_base_matches(revision, place):
            raise ValidationError(_("Администратор изменил карточку. Начните правки заново с текущей версии."))
    except ValidationError as exc:
        form.add_error(None, exc)
        return place, revision, form

    old_working_snapshot = copy.deepcopy(
        {**content_snapshot(place), **revision.payload} if revision and revision.status != VolunteerPlaceRevision.Status.APPROVED else content_snapshot(place)
    )
    for name in ("additional_info", "extra_conditions"):
        old_working_snapshot.setdefault(name, getattr(place, name))
    candidate = form.instance
    duplicate = None
    if not place.pk:
        # Serialize new-card creation for one volunteer. A browser double-click
        # or two tabs must not create two indistinguishable working cards.
        locked_creator = get_user_model().objects.select_for_update().get(pk=user.pk)
        duplicate = find_creator_duplicate(creator=locked_creator, candidate=candidate)
        if duplicate.place and not (
            form.cleaned_data.get("create_as_distinct_branch") and duplicate.branch_override_allowed
        ):
            form.duplicate_existing_place_id = duplicate.place.pk
            form.add_error(None, t("Карточка с таким названием уже есть. Откройте её или подтвердите отдельный филиал с другим адресом или координатами.", "Bu adda kart artıq mövcuddur. Onu açın və ya fərqli ünvan və ya koordinatları olan ayrıca filialı təsdiqləyin.", "A card with this name already exists. Open it or confirm a separate branch with a different address or coordinates."))
            return place, revision, form
        place.name = candidate.name
        place.category_id = candidate.category_id
        place.save()
    # Duplicate validation must finish before storage receives any new files.
    for name in ("photo", "cover_photo"):
        value = getattr(candidate, name)
        if value and not value._committed:
            value.save(value.name, value.file, save=False)
    payload = content_snapshot(candidate)
    payload["pricing_plans"] = form.cleaned_data["pricing_plans"]
    payload["structured_schedule"] = json_value(form.cleaned_schedule_days)
    from catalog.services import publication
    if revision and not revision.dependencies:
        adopt_legacy_revision(revision, place)
    revision = publication.propose(actor=user,target_type="place",target_id=place.pk,patch=payload,
        schema_version=publication.SCHEMA_VERSION,expected_version=place.content_version,
        revision_version=revision.version if revision else 0,
        submit=data.get("action") == "submit" or (source == PlaceChangeAudit.SOURCE_ADMIN and revision and revision.status == "pending"),
        explicit_save=True)
    if duplicate and duplicate.place:
        _audit_working_changes(place=place, actor=user, source=source, old_snapshot={},
            new_snapshot={'distinct_branch_confirmation': {'matched_place_id': duplicate.place.pk,
                'address': candidate.address, 'lat': candidate.lat, 'lng': candidate.lng}})
    _audit_working_changes(
        place=place,
        actor=user,
        source=source,
        old_snapshot=old_working_snapshot,
        new_snapshot={**content_snapshot(place), **revision.payload},
    )
    return place, revision, form


def save_proposal(*, user, place_id, data, files):
    return save_working_revision(
        user=user,
        place_id=place_id,
        data=data,
        files=files,
        source=PlaceChangeAudit.SOURCE_VOLUNTEER,
    )


@transaction.atomic
def restart_proposal(*, user, place_id, version):
    from catalog.services import publication
    actor=publication.fresh_actor(user);place=publication.locked_target('place',place_id)
    publication.authorize(actor,place,'place')
    if not own_places(actor).filter(pk=place_id).exists():raise PermissionDenied
    revision=get_object_or_404(VolunteerPlaceRevision.objects.select_for_update(),place=place)
    _check_version(revision,version)
    revision.payload={};revision.changed_fields=[];revision.base_snapshot=publication.snapshot(place,'place')
    revision.dependencies=publication.dependencies(place,'place');revision.base_content_version=place.content_version;revision.schema_version=publication.SCHEMA_VERSION
    revision.status='draft';revision.version+=1;revision.author=actor;revision.review_note='';revision.reviewed_by=None;revision.save()


def require_reviewer(user):
    if not (user.is_authenticated and user.is_active and user.is_staff and user.is_superuser):
        raise PermissionDenied


def review_form(revision):
    candidate = candidate_from_payload(revision.place, revision.payload)
    # Files are trusted server-stored names, never taken from a review POST.
    data = {k: v for k, v in {**content_snapshot(revision.place), **revision.payload}.items() if k not in {"photo", "cover_photo", "gallery", "nature", "operating_state"}}
    stored_district = str(data.get("district") or "").strip()
    if stored_district.startswith("baku_"):
        data["region"] = "baku"
    elif stored_district == "baku":
        data["region"] = "baku"
        data["district"] = ""
    elif stored_district:
        data["region"] = stored_district
        data["district"] = ""
    else:
        data["region"] = ""
    data["pricing_plans"] = json.dumps(data.get("pricing_plans", []))
    data["structured_schedule"] = dump_schedule_payload(data.get("structured_schedule", []))
    data.update(base_token=base_token(revision.place), revision_version=revision.version)
    form = VolunteerPlaceForm(data, instance=candidate)
    # Review reads this trusted, saved candidate, never an arbitrary review POST.
    # The shared readiness evaluator expects nested plans in cleaned_data.
    from django import forms
    form.fields['nested_pricing'] = forms.JSONField(required=False)
    form.location_publication_required = True
    return form


def adopt_legacy_revision(revision, place):
    """Upgrade captured legacy candidates only when their original base matches."""
    from catalog.services import publication
    if not revision_base_matches(revision,place):raise ValidationError("Legacy candidate source conflict.")
    base=publication.snapshot(place,'place')
    normalized=publication._validate_patch(place,'place',{k:v for k,v in revision.payload.items() if k in base})
    revision.payload={k:v for k,v in normalized.items() if v!=base[k]}
    revision.base_snapshot=base;revision.changed_fields=sorted(revision.payload)
    revision.schema_version=publication.SCHEMA_VERSION;revision.base_content_version=place.content_version
    revision.dependencies=publication.dependencies(place,'place');revision.save()


@transaction.atomic
def review_proposal(*, user, place_id, version, approve, note=""):
    from catalog.services import publication
    place=publication.locked_target('place',place_id)
    revision=get_object_or_404(VolunteerPlaceRevision.objects.select_for_update(),place=place)
    _check_version(revision,version)
    if not revision.dependencies:adopt_legacy_revision(revision,place)
    before=live_snapshot(place)
    result=publication.review(actor=user,revision_id=revision.pk,version=version,approve=approve,note=note)
    if approve:
        place.refresh_from_db()
        _audit_working_changes(place=place,actor=user,source=PlaceChangeAudit.SOURCE_ADMIN,old_snapshot=before,new_snapshot=live_snapshot(place))
    return result
