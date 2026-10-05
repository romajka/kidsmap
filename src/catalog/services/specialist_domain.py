"""D08 person claims and explicitly consented historical employment.

Claim lock order: sorted applicant/reviewer Users -> Specialist -> claim.
Employment lock order: sorted participant Users -> Organization -> Specialist
-> employment. Authorship and business grants are
never evidence of person identity or either side's employment consent.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from catalog.models import Organization, Specialist
from catalog.models.specialist_domain import (
    SpecialistClaim, SpecialistEmployment, SpecialistEmploymentEvent,
)
from catalog.services.staff_roles import is_volunteer


def require_actor(actor):
    if not getattr(actor, 'is_authenticated', False) or not actor.pk:
        raise PermissionDenied('Authenticated active account required.')
    fresh = get_user_model().objects.filter(pk=actor.pk, is_active=True).first()
    if fresh is None:
        raise PermissionDenied('Authenticated active account required.')
    return fresh


def _lock_users(ids):
    return {user.pk: user for user in get_user_model().objects.select_for_update()
            .filter(pk__in={pk for pk in ids if pk}).order_by('pk')}


def lock_actor(actor):
    actor = require_actor(actor)
    fresh = _lock_users([actor.pk]).get(actor.pk)
    if fresh is None or not fresh.is_active:
        raise PermissionDenied('Authenticated active account required.')
    return fresh


def require_person(actor, specialist):
    actor = require_actor(actor)
    if (specialist.verified_person_user_id != actor.pk or not specialist.person_verified_at):
        raise PermissionDenied('Verified person account required.')
    return actor


def _reviewer(actor):
    actor = require_actor(actor)
    if not actor.is_staff or is_volunteer(actor) or not actor.has_perm('catalog.review_specialist_claim'):
        raise PermissionDenied('Dedicated person claim reviewer required.')
    return actor


def _version(item, expected):
    if isinstance(expected, bool) or not isinstance(expected, (str, int)):
        raise ValidationError('A current version is required.', code='stale_version')
    try:
        value = int(expected)
    except (TypeError, ValueError):
        raise ValidationError('A current version is required.', code='stale_version')
    if value < 1 or value != item.version:
        raise ValidationError('The record changed; reload before deciding.', code='stale_version')


def propose_person(*, actor, name, **values):
    actor = require_actor(actor)
    allowed = {'name_alt', 'bio_az', 'bio_ru', 'bio_en', 'consultation_format'}
    if set(values) - allowed:
        raise ValidationError('Person ownership and verification cannot be proposed.')
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Person name is required.')
    with transaction.atomic():
        actor = lock_actor(actor)
        person = Specialist(name=name.strip(), created_by=actor, owner=None,
                            status=Specialist.STATUS_DRAFT, **values)
        person.full_clean()
        person.save()
        return person


@transaction.atomic
def request_claim(*, actor, specialist_id):
    actor = lock_actor(actor)
    person = Specialist.objects.select_for_update().get(pk=specialist_id)
    if person.verified_person_user_id:
        raise ValidationError('This person already has a verified account.', code='claim_conflict')
    item, _ = SpecialistClaim.objects.get_or_create(
        specialist=person, applicant=actor, status=SpecialistClaim.PENDING)
    return item


@transaction.atomic
def review_claim(*, actor, claim_id, expected_version, approve, reason=''):
    actor = _reviewer(actor)
    before = SpecialistClaim.objects.values('specialist_id', 'applicant_id').get(pk=claim_id)
    legacy_owner_id = Specialist.objects.values_list('owner_id', flat=True).get(pk=before['specialist_id'])
    users = _lock_users([actor.pk, before['applicant_id'], legacy_owner_id])
    applicant = users.get(before['applicant_id'])
    if applicant is None or not applicant.is_active:
        raise ValidationError('The applicant account is no longer active.', code='claim_conflict')
    person = Specialist.objects.select_for_update().get(pk=before['specialist_id'])
    if person.owner_id and person.owner_id not in users:
        raise ValidationError('The legacy manager changed; retry the claim decision.', code='claim_conflict')
    item = SpecialistClaim.objects.select_for_update().get(pk=claim_id, specialist=person)
    actor = _reviewer(actor)
    _version(item, expected_version)
    if item.status != SpecialistClaim.PENDING or item.applicant_id != applicant.pk:
        raise ValidationError('Only an unchanged pending claim can be decided.', code='claim_conflict')
    if not isinstance(approve, bool):
        raise ValidationError('An explicit claim decision is required.')
    if approve:
        if person.verified_person_user_id or Specialist.objects.filter(
                verified_person_user=applicant).exclude(pk=person.pk).exists():
            raise ValidationError('The person or applicant already has a verified claim.', code='claim_conflict')
        item.previous_legacy_owner_id = person.owner_id
        person.verified_person_user = applicant
        person.owner = applicant
        person.person_verified_at = timezone.now()
        person.save(update_fields=['verified_person_user', 'owner', 'person_verified_at', 'updated_at'])
    item.status = SpecialistClaim.APPROVED if approve else SpecialistClaim.REJECTED
    item.reviewed_by = actor
    item.reviewed_at = timezone.now()
    item.reason = str(reason or '')[:2000]
    item.version += 1
    item.save()
    return item


@transaction.atomic
def withdraw_claim(*, actor, claim_id, expected_version):
    actor = lock_actor(actor)
    person_id = SpecialistClaim.objects.values_list('specialist_id', flat=True).get(pk=claim_id)
    Specialist.objects.select_for_update().get(pk=person_id)
    item = SpecialistClaim.objects.select_for_update().get(pk=claim_id)
    if item.applicant_id != actor.pk:
        raise PermissionDenied('Only the applicant can withdraw a claim.')
    _version(item, expected_version)
    if item.status != SpecialistClaim.PENDING:
        raise ValidationError('Only a pending claim can be withdrawn.')
    item.status = SpecialistClaim.WITHDRAWN
    item.version += 1
    item.save(update_fields=['status', 'version', 'updated_at'])
    return item


def _parents(*, actor, specialist_id, organization_id):
    actor = require_actor(actor)
    owner_id = Organization.objects.values_list('owner_id', flat=True).get(pk=organization_id)
    person_id = Specialist.objects.values_list('verified_person_user_id', flat=True).get(pk=specialist_id)
    users = _lock_users([actor.pk, owner_id, person_id])
    actor = users.get(actor.pk)
    if actor is None or not actor.is_active:
        raise PermissionDenied('Authenticated active account required.')
    organization = Organization.objects.select_for_update().get(pk=organization_id)
    person = Specialist.objects.select_for_update().get(pk=specialist_id)
    current_ids = {pk for pk in (organization.owner_id, person.verified_person_user_id) if pk}
    if not current_ids.issubset(users):
        raise ValidationError('A participant changed; retry with current parties.', code='consent_conflict')
    return actor, organization, person


def _employment(actor, employment_id):
    before = SpecialistEmployment.objects.values('specialist_id', 'organization_id').get(pk=employment_id)
    actor, organization, person = _parents(actor=actor, **before)
    item = SpecialistEmployment.objects.select_for_update().get(pk=employment_id)
    return actor, organization, person, item


def _live_parties(organization, person):
    if organization.archived_at or not organization.owner_id:
        raise ValidationError('An active organization owner is required.')
    if not person.verified_person_user_id or not person.person_verified_at:
        raise ValidationError('The specialist must have a verified person account.')
    ids = {organization.owner_id, person.verified_person_user_id}
    if get_user_model().objects.filter(pk__in=ids, is_active=True).count() != len(ids):
        raise ValidationError('Both participant accounts must be active.')


def _party(actor, organization, person):
    if actor.pk not in {organization.owner_id, person.verified_person_user_id}:
        raise PermissionDenied('The person or direct organization owner is required.')


def _history(item, actor, action):
    SpecialistEmploymentEvent.objects.create(employment=item, actor=actor, action=action,
        version=item.version, role=item.role, start_date=item.start_date, end_date=item.end_date)


@transaction.atomic
def propose_employment(*, actor, specialist_id, organization_id, role, start_date, end_date=None):
    actor, organization, person = _parents(actor=actor,
        specialist_id=specialist_id, organization_id=organization_id)
    _party(actor, organization, person)
    _live_parties(organization, person)
    if not isinstance(role, str) or not role.strip():
        raise ValidationError('Employment role is required.')
    item = SpecialistEmployment(specialist=person, organization=organization, role=role.strip(),
        start_date=start_date, end_date=end_date, created_by=actor,
        person_user_id=person.verified_person_user_id, organization_owner_id=organization.owner_id,
        organization_ownership_version=organization.ownership_version)
    item.full_clean()
    if SpecialistEmployment.objects.filter(specialist=person, organization=organization,
            role=item.role, start_date=item.start_date, end_date=item.end_date,
            status__in=(SpecialistEmployment.PENDING, SpecialistEmployment.ACTIVE)).exists():
        raise ValidationError('This exact employment is already pending or active.', code='employment_conflict')
    item.save()
    _history(item, actor, 'proposed')
    return item


@transaction.atomic
def confirm_employment(*, actor, employment_id, side, expected_version):
    actor, organization, person, item = _employment(actor, employment_id)
    if side not in {'person', 'organization'}:
        raise ValidationError('An explicit confirmation side is required.')
    expected_actor = person.verified_person_user_id if side == 'person' else organization.owner_id
    if actor.pk != expected_actor:
        raise PermissionDenied('Only that side can give its consent.')
    _version(item, expected_version)
    if item.status != SpecialistEmployment.PENDING:
        raise ValidationError('Only a pending employment can be confirmed.')
    _live_parties(organization, person)
    if (item.person_user_id != person.verified_person_user_id
            or item.organization_owner_id != organization.owner_id
            or item.organization_ownership_version != organization.ownership_version):
        raise ValidationError('A participant changed; propose a new employment.', code='consent_conflict')
    if getattr(item, f'{side}_confirmed_at'):
        raise ValidationError('This side already confirmed the employment.')
    setattr(item, f'{side}_confirmed_by', actor)
    setattr(item, f'{side}_confirmed_at', timezone.now())
    if item.person_confirmed_at and item.organization_confirmed_at:
        item.status = SpecialistEmployment.ACTIVE
    item.version += 1
    item.full_clean()
    item.save()
    _history(item, actor, f'{side}_confirmed')
    return item


@transaction.atomic
def cancel_employment(*, actor, employment_id, expected_version):
    actor, organization, person, item = _employment(actor, employment_id)
    _party(actor, organization, person)
    _version(item, expected_version)
    if item.status == SpecialistEmployment.CANCELLED:
        raise ValidationError('The employment is already cancelled.')
    item.status = SpecialistEmployment.CANCELLED
    item.cancelled_by = actor
    item.cancelled_at = timezone.now()
    item.version += 1
    item.save()
    _history(item, actor, 'cancelled')
    return item
