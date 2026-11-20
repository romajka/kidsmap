from catalog.services.permanent_place_rules import copy

STATUS_LABELS = {
    "open": ("Открытые", "Açıq", "Open"),
    "all": ("Все", "Hamısı", "All"),
    "submitted": ("Подана", "Göndərilib", "Submitted"),
    "second_review": ("На повторной проверке", "Təkrar baxışda", "Under review"),
    "approved": ("Удовлетворена", "Təmin edilib", "Upheld"),
    "rejected": ("Отклонена", "Rədd edilib", "Denied"),
}
KIND_LABELS = {
    "place": ("Место", "Məkan", "Place"),
    "volunteer_revision": ("Заявка на публикацию", "Dərc üçün müraciət", "Publication request"),
    "publication_request": ("Заявка на публикацию места", "Məkanın dərci üçün müraciət", "Place publication request"),
    "specialist": ("Анкета специалиста", "Mütəxəssis anketi", "Specialist profile"),
    "event": ("Событие", "Tədbir", "Event"),
    "place_review": ("Отзыв о месте", "Məkan haqqında rəy", "Place review"),
    "specialist_review": ("Отзыв о специалисте", "Mütəxəssis haqqında rəy", "Specialist review"),
    "activity_review": ("Отзыв о занятии", "Məşğələ haqqında rəy", "Activity review"),
    "event_review": ("Отзыв о событии", "Tədbir haqqında rəy", "Event review"),
    "site_review": ("Отзыв о KidsMap", "KidsMap haqqında rəy", "KidsMap review"),
}


def kind_label(kind):
    return copy(*KIND_LABELS[kind])


def present(appeal):
    appeal.kind_label = kind_label(appeal.kind)
    appeal.status_label = copy(*STATUS_LABELS[appeal.status])
    return appeal
