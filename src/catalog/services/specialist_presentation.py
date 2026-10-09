"""Public consent/date presentation; no inference from names, places or authors."""
from django.utils import timezone
from catalog.models.specialist_domain import SpecialistEmployment
from catalog.services.public_presentation import visible


def public_profile_context(specialist):
    current, past, future = [], [], []
    today = timezone.localdate()
    links = specialist.employment_links.select_related(
        'organization', 'organization__owner', 'specialist__verified_person_user'
    ).order_by('-start_date', '-pk')
    for item in links:
        # An unconfirmed invitation is never public employment history.
        if not (item.person_confirmed_at and item.organization_confirmed_at):
            continue
        org = item.organization
        if not visible(org):
            continue
        person = item.specialist
        live_consent = bool(
            person.verified_person_user_id and person.person_verified_at
            and person.verified_person_user.is_active
            and org.owner_id and org.owner.is_active
            and item.person_user_id == person.verified_person_user_id
            and item.person_confirmed_by_id == person.verified_person_user_id
            and item.organization_owner_id == org.owner_id
            and item.organization_confirmed_by_id == org.owner_id
            and item.organization_ownership_version == org.ownership_version
        )
        if item.status == SpecialistEmployment.CANCELLED or (item.end_date and item.end_date < today):
            item.temporal_state = 'history'
            past.append(item)
        elif item.status == SpecialistEmployment.ACTIVE and live_consent:
            if item.start_date > today:
                item.temporal_state = 'future'
                future.append(item)
            else:
                item.temporal_state = 'current'
                current.append(item)

    from catalog.services.features import is_organizations_section_enabled
    orgs_enabled = is_organizations_section_enabled()
    for item in current + past + future:
        item.organization_linkable = orgs_enabled and visible(item.organization)

    active_locs = list(specialist.practice_locations.filter(is_active=True)
        .select_related('place', 'region', 'district', 'metro'))
    for loc in active_locs:
        loc.is_place_visible = bool(loc.place and visible(loc.place))

    return {
        'specialist_current_employment': current,
        'specialist_past_employment': past,
        'specialist_future_employment': future,
        'specialist_active_practice_locations': active_locs,
        'organizations_section_enabled': orgs_enabled,
        # Retired private addresses stay visible only in the person's workspace.
        'practice_history': [],
    }
