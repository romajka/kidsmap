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
    from types import SimpleNamespace
    from catalog.services.place_identity import identity_registry, check_duplicates
    owned = Place.objects.filter(created_by=creator, deleted_at__isnull=True)
    snapshot = identity_registry(creator, places=owned)
    result = check_duplicates(creator, candidate, registry=snapshot)
    matches = [row for row in result['results'] if any('name' in e['signals'] for e in row['evidence'])]
    if not matches:
        return DuplicateDecision(None, False)
    conflicting = next((row for row in matches if
        not _distinct_location(SimpleNamespace(**row['versions'][-1]['fields']), candidate) or
        any(e['classification']=='confirmed' for e in row['evidence'])), None)
    selected = conflicting or matches[0]
    return DuplicateDecision(owned.get(pk=selected['id']), conflicting is None)
