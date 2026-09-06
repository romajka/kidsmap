from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_gallery_order(order, saved_ids, deleted_ids, new_count):
    if order is None:
        return
    expected = {f'saved:{pk}' for pk in saved_ids if str(pk) not in set(map(str, deleted_ids))}
    expected.update(f'new:{index}' for index in range(new_count))
    if not isinstance(order, list) or any(not isinstance(key, str) for key in order) or len(order) != len(expected) or set(order) != expected:
        raise ValidationError(_('Порядок фотографий изменился. Проверьте галерею и повторите сохранение.'))


def apply_gallery_order(place, form):
    order = form.cleaned_data.get('gallery_order')
    if order is None:
        return
    photos = list(place.gallery.order_by('pk'))
    previous = set(form.photo_gallery_ids)
    new = [photo for photo in photos if photo.pk not in previous]
    mapping = {f'saved:{photo.pk}': photo for photo in photos if photo.pk in previous}
    mapping.update({f'new:{index}': photo for index, photo in enumerate(new)})
    for index, key in enumerate(order):
        photo = mapping[key]
        photo.order = index
    if photos:
        type(photos[0]).objects.bulk_update(photos, ['order'])
