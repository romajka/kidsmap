"""One new-publication contract for owner, reviewer and admin entry surfaces."""
from django.utils import timezone
from catalog.services.event_presentation import detail_errors
from catalog.services.phone_numbers import contact_copy


def publication_errors(event):
    errors = detail_errors(event)
    required = {
        'name_az': (event.name_az, ('Укажите название на AZ.', 'AZ dilində adı daxil edin.', 'Enter the AZ title.')),
        'category': (event.category_id, ('Выберите категорию.', 'Kateqoriya seçin.', 'Choose a category.')),
        'description_az': (event.description_az, ('Добавьте описание на AZ.', 'AZ dilində təsvir əlavə edin.', 'Add the AZ description.')),
        'photo': (event.photo, ('Добавьте обложку.', 'Üz qabığı əlavə edin.', 'Add a cover image.')),
    }
    for field, (value, messages) in required.items():
        if not value or isinstance(value, str) and not value.strip():
            errors[field] = contact_copy(*messages)
    if bool(event.organizer_organization_id) == bool(event.organizer_specialist_id):
        errors['organizer_organization'] = contact_copy('Выберите одного организатора.', 'Bir təşkilatçı seçin.', 'Choose one organizer.')
    start, end = event.start_datetime, event.end_datetime
    if not start or timezone.is_naive(start):
        errors['start_datetime'] = contact_copy('Укажите начало мероприятия.', 'Tədbirin başlama vaxtını daxil edin.', 'Enter the event start.')
    if not end or timezone.is_naive(end):
        errors['end_datetime'] = contact_copy('Укажите окончание мероприятия.', 'Tədbirin bitmə vaxtını daxil edin.', 'Enter the event end.')
    elif not errors.get('start_datetime') and end <= start:
        errors['end_datetime'] = contact_copy('Окончание должно быть позже начала.', 'Bitmə vaxtı başlama vaxtından sonra olmalıdır.', 'The end must follow the start.')
    elif end <= timezone.now():
        errors['end_datetime'] = contact_copy('Мероприятие уже завершилось.', 'Tədbir artıq bitib.', 'The event has already ended.')
    if event.price_mode == 'legacy' and not str(event.price_text or '').strip():
        errors['price_mode'] = contact_copy('Выберите цену или «Уточнить».', 'Qiymət və ya «Dəqiqləşdirin» seçin.', 'Choose a price or Ask for price.')
    if not event.registration['url']:
        field = {'phone':'phone', 'whatsapp':'whatsapp', 'link':'registration_url'}.get(event.registration_method, 'registration_method')
        errors.setdefault(field, contact_copy('Укажите выбранный способ записи.', 'Seçilmiş qeydiyyat üsulunu doldurun.', 'Complete the selected registration method.'))
    if event.event_format != 'online':
        address = event.address
        if event.related_place_id:
            # Same source as capture_venue_snapshot; permission/availability remains domain-owned.
            address = event.related_place.address
        if not str(address or '').strip():
            errors['address'] = contact_copy('Укажите адрес площадки.', 'Məkanın ünvanını daxil edin.', 'Enter the venue address.')
    return errors


def required_missing(event):
    return list(publication_errors(event).values())


def has_possible_duplicate(event):
    from catalog.models import Event
    if not event.start_datetime or not str(event.name_az or '').strip():
        return False
    if bool(event.organizer_organization_id) == bool(event.organizer_specialist_id):
        return False
    return Event.objects.filter(deleted_at__isnull=True,
        organizer_organization_id=event.organizer_organization_id,
        organizer_specialist_id=event.organizer_specialist_id,
        name_az__iexact=event.name_az.strip(), start_datetime=event.start_datetime).exclude(pk=event.pk).exists()
