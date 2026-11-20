"""Release metadata shared by the public documents and the consent ledger."""
from dataclasses import dataclass
from datetime import date

from django.utils.formats import date_format
from django.utils.translation import override


@dataclass(frozen=True)
class Release:
    version: str
    published_on: date
    updated_on: date
    generation: int


# Bump the version and date on publication. Bump generation only when users
# must make a new choice. Existing accounts have no implied baseline receipt.
RELEASES = {
    "terms": Release("1.0", date(2026, 6, 22), date(2026, 9, 3), 1),
    "privacy": Release("1.0", date(2026, 6, 22), date(2026, 10, 20), 1),
}


def public_metadata(slug, language):
    release = RELEASES[slug]
    with override(language):
        return {"legal_version": release.version, "updated_date": date_format(release.updated_on)}
