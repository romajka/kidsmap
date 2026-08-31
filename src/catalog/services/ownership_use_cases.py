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
    if not request.user.is_authenticated:
        return OwnershipRequestResult(
            ok=False,
            created=False,
            message=_("Для отправки заявки войдите в аккаунт и повторите действие."),
        )

    if place.owner_id == request.user.id:
        return OwnershipRequestResult(
            ok=False,
            created=False,
            message=_("Этот кружок уже привязан к вашему аккаунту."),
        )

    existing = ownership_repository.latest_for_user_and_place(user=request.user, place=place)
    if existing and existing.status == PlaceOwnershipRequest.STATUS_PENDING:
        return OwnershipRequestResult(
            ok=False,
            created=False,
            message=_("У вас уже есть активная заявка по этому кружку. Дождитесь решения модератора в кабинете."),
            ownership_request=existing,
        )

    note = (request.POST.get("note") or "").strip()
    created_request = ownership_repository.create_pending(place=place, applicant=request.user, note=note)

    return OwnershipRequestResult(
        ok=True,
        created=True,
        message=_("Заявка отправлена. После проверки модератором вы получите доступ к карточке."),
        ownership_request=created_request,
    )
