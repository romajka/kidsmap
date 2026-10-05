"""Extend the existing unlink/anonymize policy to specialist identity authority.

Historical person/profile/review/location/employment records and document bytes
are retained. This hook introduces no new byte-retention or deletion policy.
The caller holds the account lock inside account-deletion's transaction.
"""
from django.db.models import Q, F

from catalog.models import (Organization, Specialist, SpecialistClaim, SpecialistDocument,
    SpecialistEmployment, SpecialistEmploymentEvent)


def unlink_specialist_identity(*, user_id, now):
    affected = SpecialistEmployment.objects.filter(
        Q(person_user_id=user_id) | Q(organization_owner_id=user_id)
        | Q(person_confirmed_by_id=user_id) | Q(organization_confirmed_by_id=user_id))
    organization_ids = list(affected.values_list('organization_id', flat=True))
    list(Organization.objects.select_for_update().filter(pk__in=organization_ids).order_by('pk'))
    person_ids = set(affected.values_list('specialist_id', flat=True))
    person_ids.update(Specialist.objects.filter(Q(owner_id=user_id) | Q(verified_person_user_id=user_id))
                      .values_list('pk', flat=True))
    list(Specialist.objects.select_for_update().filter(pk__in=person_ids).order_by('pk'))
    links = list(affected.select_for_update().order_by('pk'))
    revoked = 0
    for link in links:
        if link.status in {'pending', 'active'}:
            link.status = 'cancelled'
            link.cancelled_at = now
            link.cancelled_by = None
            link.version += 1
            link.save(update_fields=['status', 'cancelled_at', 'cancelled_by', 'version', 'updated_at'])
            SpecialistEmploymentEvent.objects.create(employment=link, action='account_unlinked', actor=None,
                version=link.version, role=link.role, start_date=link.start_date, end_date=link.end_date)
            revoked += 1
    SpecialistClaim.objects.filter(applicant_id=user_id, status='pending').update(
        status='withdrawn', version=F('version') + 1, updated_at=now)
    claims = SpecialistClaim.objects.filter(Q(applicant_id=user_id) | Q(reviewed_by_id=user_id)
                                            | Q(previous_legacy_owner_id=user_id))
    anonymized = claims.update(reason='')
    consent = SpecialistDocument.objects.filter(Q(opted_in_by_id=user_id)
                  | Q(specialist__verified_person_user_id=user_id))
    revoked_documents = consent.update(is_published=False, opted_in_by=None, opted_in_at=None)
    unlinked = Specialist.objects.filter(verified_person_user_id=user_id).update(
        owner=None, verified_person_user=None, person_verified_at=None)
    return {'specialist_persons_unlinked': unlinked, 'specialist_document_consents_revoked': revoked_documents,
            'specialist_claim_notes_anonymized': anonymized, 'specialist_employments_revoked': revoked}
