from catalog.models.place import Place, Event
from catalog.models.review import PlaceReview
from catalog.models.owner import PlaceOwnershipRequest

class ModerationPlace(Place):
    class Meta:
        proxy = True
        app_label = 'catalog_moderation'
        verbose_name = 'Места на проверке'
        verbose_name_plural = 'Места на проверке'

class ModerationEvent(Event):
    class Meta:
        proxy = True
        app_label = 'catalog_moderation'
        verbose_name = 'Мероприятия на проверке'
        verbose_name_plural = 'Мероприятия на проверке'

class ModerationReview(PlaceReview):
    class Meta:
        proxy = True
        app_label = 'catalog_moderation'
        verbose_name = 'Отзывы на проверке'
        verbose_name_plural = 'Отзывы на проверке'

class ModerationPlaceOwnershipRequest(PlaceOwnershipRequest):
    class Meta:
        proxy = True
        app_label = 'catalog_moderation'
        verbose_name = 'Заявки владельцев'
        verbose_name_plural = 'Заявки владельцев'
