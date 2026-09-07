"""Proposed edits stay separate from live Place until atomic Superadmin review."""
import copy
import hashlib
import json

from django.core import signing
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
    for name in ("name", "slug", "owner_id", "created_by_id", "is_active", "status", "is_verified", "deleted_at"):
        result[name] = json_value(getattr(place, name))
    return result


def base_token(place):
    digest = hashlib.sha256(json.dumps(live_snapshot(place), sort_keys=True).encode()).hexdigest()
    return signing.dumps({"place": place.pk, "digest": digest}, salt="volunteer-place")


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
    for name in CONTENT_FIELDS:
        if name in payload:
            field = Place._meta.get_field(name)
            setattr(candidate, field.attname, field.to_python(payload[name]) if not field.is_relation else payload[name])
    candidate.pricing_plans = payload.get("pricing_plans", place.pricing_plans)
    return candidate


def editor_form(place, revision=None, *, data=None, files=None):
    payload = revision.payload if revision and revision.status != "approved" else content_snapshot(place)
    candidate = candidate_from_payload(place, payload)
    initial = {"base_token": base_token(place), "revision_version": revision.version if revision else 0}
    form = VolunteerPlaceForm(data, files, instance=candidate, initial=initial)
    if data is None:
        raw_schedule = dump_schedule_payload(payload.get("structured_schedule", []))
        form.initial["structured_schedule"] = raw_schedule
        form.fields["structured_schedule"].initial = raw_schedule
        form.schedule_editor_payload = raw_schedule
        form.schedule_editor_days = payload.get("structured_schedule", [])
    return form


def _check_version(revision, version):
    if version != (revision.version if revision else 0):
        raise ValidationError(_("Данные уже изменились. Обновите страницу перед сохранением."))


@transaction.atomic
def save_proposal(*, user, place_id, data, files):
    places = own_places(user)
    place = get_object_or_404(places.select_for_update(), pk=place_id) if place_id else Place(created_by=user, status="draft", is_active=False)
    revision = VolunteerPlaceRevision.objects.filter(place=place).first() if place.pk else None
    form = editor_form(place, revision, data=data, files=files)
    if not form.is_valid():
        return place, revision, form
    try:
        _check_version(revision, form.cleaned_data["revision_version"])
        if not token_matches(form.cleaned_data["base_token"], place):
            raise ValidationError(_("Карточка изменилась. Обновите страницу."))
        if revision and revision.status != "approved" and revision.base_snapshot != live_snapshot(place):
            raise ValidationError(_("Администратор изменил карточку. Начните правки заново с текущей версии."))
    except ValidationError as exc:
        form.add_error(None, exc)
        return place, revision, form
    candidate = form.instance
    # FileField storage creates unique names. Never overwrite/delete a live file.
    for name in ("photo", "cover_photo"):
        value = getattr(candidate, name)
        if value and not value._committed:
            value.save(value.name, value.file, save=False)
    if not place.pk:
        place.name = candidate.name
        place.category_id = candidate.category_id
        place.save()
    payload = content_snapshot(candidate)
    payload["pricing_plans"] = form.cleaned_data["pricing_plans"]
    payload["structured_schedule"] = json_value(form.cleaned_schedule_days)
    if revision is None:
        revision = VolunteerPlaceRevision(place=place, author=user)
    elif revision.status == "approved":
        revision.base_snapshot = {}
    revision.base_snapshot = revision.base_snapshot or live_snapshot(place)
    revision.payload = json_value(payload)
    revision.author = user
    keep_feedback = data.get("action") == "draft" and revision.status in {"rejected", "draft"}
    revision.status = "pending" if data.get("action") == "submit" else "draft"
    if not keep_feedback:
        revision.review_note = ""
        revision.reviewed_by = None
    revision.version = (revision.version + 1) if revision.pk else 1
    revision.save()
    return place, revision, form


@transaction.atomic
def restart_proposal(*, user, place_id, version):
    place = get_object_or_404(own_places(user).select_for_update(), pk=place_id)
    revision = get_object_or_404(VolunteerPlaceRevision, place=place)
    _check_version(revision, version)
    revision.payload = content_snapshot(place)
    revision.base_snapshot = live_snapshot(place)
    revision.status = "draft"
    revision.version += 1
    revision.review_note = ""
    revision.reviewed_by = None
    revision.save()


def require_reviewer(user):
    if not (user.is_authenticated and user.is_active and user.is_staff and user.is_superuser):
        raise PermissionDenied


def review_form(revision):
    candidate = candidate_from_payload(revision.place, revision.payload)
    # Files are trusted server-stored names, never taken from a review POST.
    data = {k: v for k, v in revision.payload.items() if k not in {"photo", "cover_photo"}}
    data["pricing_plans"] = json.dumps(data.get("pricing_plans", []))
    data["structured_schedule"] = dump_schedule_payload(data.get("structured_schedule", []))
    data.update(base_token=base_token(revision.place), revision_version=revision.version)
    return VolunteerPlaceForm(data, instance=candidate)


@transaction.atomic
def review_proposal(*, user, place_id, version, approve, note=""):
    require_reviewer(user)
    # Same lock order as volunteer saves: Place, then its revision.
    place = get_object_or_404(Place.objects.select_for_update(), pk=place_id)
    revision = get_object_or_404(VolunteerPlaceRevision.objects.select_for_update(), place=place)
    _check_version(revision, version)
    if revision.status != "pending":
        raise ValidationError(_("Эти изменения уже рассмотрены или ещё не отправлены."))
    if place.deleted_at or place.owner_id or place.created_by_id != revision.author_id or revision.author_id is None:
        raise ValidationError(_("Место удалено или передано другому владельцу. Одобрение недоступно."))
    if approve:
        if revision.base_snapshot != live_snapshot(place):
            raise ValidationError(_("Карточка изменилась после отправки. Верните её волонтёру на доработку."))
        form = review_form(revision)
        if not form.is_valid():
            raise ValidationError(_("В предложенных изменениях есть ошибки: %(errors)s") % {"errors": form.errors.as_text()})
        readiness = evaluate_form_readiness(form, form.instance)
        if not readiness.is_ready:
            raise ValidationError(publication_blocked_message(readiness))
        old = live_snapshot(place)
        candidate = form.instance
        candidate.name = next((getattr(candidate, f"name_{lang}") for lang in ("az", "ru", "en") if getattr(candidate, f"name_{lang}")), place.name)
        candidate.pricing_plans = form.cleaned_data["pricing_plans"]
        candidate.status = Place.STATUS_PUBLISHED
        candidate.is_active = True
        candidate.published_at = place.published_at or timezone.now()
        candidate.rejection_reason = ""
        candidate.save()
        form.save_schedule(candidate)
        new = live_snapshot(candidate)
        PlaceChangeAudit.objects.bulk_create([
            PlaceChangeAudit(place=place, changed_by=user, source=PlaceChangeAudit.SOURCE_ADMIN,
                             field_name=key, old_value=json.dumps(old.get(key), ensure_ascii=False),
                             new_value=json.dumps(value, ensure_ascii=False))
            for key, value in new.items() if old.get(key) != value
        ])
        revision.status = "approved"
    else:
        if not note.strip():
            raise ValidationError(_("Укажите, что нужно исправить."))
        revision.status = "rejected"
    revision.review_note = note.strip()
    revision.reviewed_by = user
    revision.version += 1
    revision.save()
    return revision
