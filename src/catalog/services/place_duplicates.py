from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from catalog.models import Place


def normalize_place_name(place) -> str:
    return next((_normalize(getattr(place, field, "")) for field in ("name_az", "name_ru", "name_en", "name") if _normalize(getattr(place, field, ""))), "")


def _normalize(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value or "").strip()).casefold()


def _names(place):
    return {_normalize(getattr(place, field, "")) for field in ("name_az", "name_ru", "name_en", "name")} - {""}


def _distinct_location(existing, candidate):
    address, other_address = _normalize(existing.address), _normalize(candidate.address)
    return bool(address and other_address and address != other_address) or (
        existing.lat is not None and existing.lng is not None
        and candidate.lat is not None and candidate.lng is not None
        and (existing.lat != candidate.lat or existing.lng != candidate.lng)
    )


@dataclass(frozen=True, slots=True)
class DuplicateDecision:
    place: Place | None
    branch_override_allowed: bool


def find_creator_duplicate(*, creator, candidate) -> DuplicateDecision:
    from catalog.services.volunteer_places import candidate_from_payload
    names = _names(candidate)
    if not names:
        return DuplicateDecision(None, False)
    matches = []
    for place in Place.objects.filter(created_by=creator, deleted_at__isnull=True).select_related('volunteer_revision').order_by('pk'):
        revision = getattr(place, 'volunteer_revision', None)
        current = candidate_from_payload(place, revision.payload) if revision and revision.status != 'approved' else place
        # The fallback Place.name may still refer to an old working name.
        if revision and revision.status != 'approved':
            current.name = next((getattr(current, f'name_{lang}') for lang in ('az', 'ru', 'en') if getattr(current, f'name_{lang}')), '')
        if names & _names(current):
            matches.append((place, current))
    if not matches:
        return DuplicateDecision(None, False)
    conflicting = next((place for place, current in matches if not _distinct_location(current, candidate)), None)
    return DuplicateDecision(conflicting or matches[0][0], conflicting is None)
