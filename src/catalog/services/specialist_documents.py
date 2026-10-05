"""Person consent and private-document authorization are independent of business grants."""
from pathlib import Path
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from catalog.models import Specialist, SpecialistDocument
from catalog.services.staff_roles import is_volunteer


def _advance_document_epoch(person):
    """Caller holds the person row lock; share its timestamp without schema drift.

    QuerySet.update deliberately avoids auto_now replacing a monotonic value.
    Any document decision invalidates all person document/profile form tokens.
    """
    epoch = max(timezone.now(), person.updated_at + timedelta(microseconds=1))
    Specialist.objects.filter(pk=person.pk).update(updated_at=epoch)
    person.updated_at = epoch


def can_review_documents(user):
    if not user.is_authenticated or not user.pk:
        return False
    from django.contrib.auth import get_user_model
    fresh = get_user_model().objects.filter(pk=user.pk, is_active=True, is_staff=True).first()
    return bool(fresh and not is_volunteer(fresh)
                and fresh.has_perm('catalog.review_specialist_documents'))


def is_person(user, specialist):
    from django.contrib.auth import get_user_model
    return bool(user.is_authenticated and specialist.verified_person_user_id
                and specialist.verified_person_user_id == user.pk and specialist.person_verified_at
                and get_user_model().objects.filter(pk=user.pk, is_active=True).exists())


def is_public_document(document):
    person = document.specialist
    return bool(document.document_type in {'diploma', 'certificate'}
                and document.status == 'approved' and document.is_published
                and document.opted_in_at and document.opted_in_by_id
                and document.opted_in_by_id == person.verified_person_user_id
                and person.person_verified_at and person.status == 'published' and person.is_active
                and person.verified_person_user.is_active)


def can_download_document(user, document):
    return is_person(user, document.specialist) or can_review_documents(user) or is_public_document(document)


def upload_document(*, actor, specialist_id, uploaded_file, document_type, name):
    if document_type not in {'identity', 'diploma', 'certificate'}:
        raise ValidationError('Unknown document type')
    if uploaded_file.size > 10 * 1024 * 1024 or uploaded_file.size == 0:
        raise ValidationError('Document must be between 1 byte and 10 MiB')
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {'.pdf', '.png', '.jpg', '.jpeg'}:
        raise ValidationError('Use PDF, PNG or JPEG')
    with transaction.atomic():
        from django.contrib.auth import get_user_model
        actor = get_user_model().objects.select_for_update().get(pk=actor.pk)
        person = Specialist.objects.select_for_update().get(pk=specialist_id)
        if not is_person(actor, person):
            raise PermissionError('Verified specialist person required')
        document = SpecialistDocument.objects.create(specialist=person, document_type=document_type,
                name=name, file=uploaded_file, status='pending', is_published=False)
        _advance_document_epoch(person)
        return document


def set_document_public_choice(*, actor, document_id, publish):
    if not isinstance(publish, bool):
        raise ValidationError('An explicit boolean publication choice is required')
    with transaction.atomic():
        from django.contrib.auth import get_user_model
        actor = get_user_model().objects.select_for_update().get(pk=actor.pk)
        # Person first, then document: same order as ownership/account deletion operations.
        person_id = SpecialistDocument.objects.values_list('specialist_id', flat=True).get(pk=document_id)
        person = Specialist.objects.select_for_update().get(pk=person_id)
        document = SpecialistDocument.objects.select_for_update().get(pk=document_id, specialist=person)
        if not is_person(actor, person):
            raise PermissionError('Verified specialist person required')
        if publish and document.document_type == 'identity':
            raise ValidationError('Identity evidence is always private')
        document.is_published = bool(publish)
        document.opted_in_by = actor if publish else None
        document.opted_in_at = timezone.now() if publish else None
        document.save(update_fields=['is_published', 'opted_in_by', 'opted_in_at'])
        _advance_document_epoch(person)
        document.specialist = person
        return document


def review_document(*, actor, document_id, approve, reason=''):
    if not isinstance(approve, bool):
        raise ValidationError('An explicit boolean review decision is required')
    if not can_review_documents(actor):
        raise PermissionError('Dedicated document reviewer required')
    with transaction.atomic():
        from catalog.services.specialist_domain import lock_actor
        actor = lock_actor(actor)
        person_id = SpecialistDocument.objects.values_list('specialist_id', flat=True).get(pk=document_id)
        person = Specialist.objects.select_for_update().get(pk=person_id)
        document = SpecialistDocument.objects.select_for_update().get(pk=document_id, specialist=person)
        if not can_review_documents(actor):
            raise PermissionError('Document review permission revoked')
        document.status = 'approved' if approve else 'rejected'
        document.rejection_reason = '' if approve else str(reason)[:2000]
        document.save(update_fields=['status', 'rejection_reason'])
        _advance_document_epoch(person)
        document.specialist = person
        return document
