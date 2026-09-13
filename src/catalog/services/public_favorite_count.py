from dataclasses import dataclass

from catalog.models import SiteSettings
from catalog.services.favorite_metrics import eligible_favorites_count


@dataclass(frozen=True, slots=True)
class PublicFavoriteCount:
    visible: bool
    count: int | None


def build_public_favorite_count(*, place_id: int, site_settings: SiteSettings | None = None):
    site_settings = site_settings or SiteSettings.get_solo()
    if not site_settings.public_favorites_count_enabled or site_settings.public_favorites_minimum is None:
        return PublicFavoriteCount(False, None)
    count = eligible_favorites_count(place_id=place_id)
    if count < site_settings.public_favorites_minimum:
        return PublicFavoriteCount(False, None)
    return PublicFavoriteCount(True, count)
