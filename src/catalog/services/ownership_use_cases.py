from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.interfaces.repositories import IPlaceOwnershipRequestRepository
from catalog.models import Place, PlaceOwnershipRequest


@dataclass(slots=True)
class OwnershipRequestResult:
    ok: bool
    created: bool
    message: str
    ownership_request: PlaceOwnershipRequest | None = None


def submit_place_ownership_request(
    *,
    request,
    place: Place,
    ownership_repository: IPlaceOwnershipRequestRepository,
) -> OwnershipRequestResult:
    from django.core.exceptions import PermissionDenied, ValidationError
    from catalog.services.organization_ownership import submit_claim
    try:
        item=submit_claim(actor=request.user,target_type='place',target_id=place.pk,note=(request.POST.get('note') or '').strip())
    except (PermissionDenied, ValidationError):
        return OwnershipRequestResult(ok=False,created=False,message=_("Заявка недоступна или уже требует проверки."))
    return OwnershipRequestResult(ok=True,created=True,message=_("Заявка отправлена. Проверка владения не публикует карточку."),ownership_request=item)
