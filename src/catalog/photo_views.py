"""Photo preparation and retry-safe AJAX saves for the owner wizard."""
import hashlib
import logging
from io import BytesIO
from uuid import UUID

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from PIL import Image, ImageOps
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.services.image_uploads import normalize_uploaded_image, MAX_IMAGE_BATCH_BYTES
from catalog.services.permanent_place_rules import copy as t

logger = logging.getLogger(__name__)


@never_cache
@require_GET
def owner_photo_thumbnail(request, pk, photo_id):
    if not request.user.is_authenticated:
        return HttpResponse(status=403)
    from catalog.repositories.django_repositories import DjangoOwnerPlaceRepository
    from catalog.services.image_uploads import MAX_IMAGE_SOURCE_PIXELS, MAX_IMAGE_SOURCE_DIMENSION
    place = get_object_or_404(DjangoOwnerPlaceRepository().managed_queryset(user=request.user), pk=pk)
    field = get_object_or_404(place.gallery, pk=photo_id).image if photo_id else place.photo
    if not field:
        return HttpResponse(status=404)
    try:
        with field.open('rb') as source, Image.open(source) as image:
            if image.width * image.height > MAX_IMAGE_SOURCE_PIXELS or max(image.size) > MAX_IMAGE_SOURCE_DIMENSION:
                return HttpResponse(status=422)
            image.thumbnail((320, 320), Image.Resampling.LANCZOS)
            ImageOps.exif_transpose(image, in_place=True)
            image.info.clear()
            output = BytesIO()
            image.save(output, format='WEBP', quality=76)
            return HttpResponse(output.getvalue(), content_type='image/webp')
    except (OSError, ValueError):
        return HttpResponse(status=422)


@never_cache
@require_POST
def prepare_owner_photo(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': t('Войдите в аккаунт.', 'Hesaba daxil olun.', 'Please sign in.')}, status=403)
    uploads = [file for _, files in request.FILES.lists() for file in files]
    if len(uploads) != 1 or 'photo' not in request.FILES:
        return JsonResponse({'error': t('Выберите одну фотографию.', 'Bir şəkil seçin.', 'Choose one photo.')}, status=422)
    key = f'photo-prepare:{request.user.pk}'
    if not cache.add(key, True, timeout=120):
        return JsonResponse({'error': t('Дождитесь обработки предыдущего фото и повторите.', 'Əvvəlki şəklin hazırlanmasını gözləyin və təkrarlayın.', 'Wait for the previous photo and retry.')}, status=429)
    try:
        normalized = normalize_uploaded_image(uploads[0])
        return HttpResponse(normalized.read(), content_type='image/webp')
    except ValidationError as exc:
        return JsonResponse({'error': ' '.join(exc.messages)}, status=422)
    except Exception:
        logger.exception('Photo preparation failed for user %s', request.user.pk)
        return JsonResponse({'error': t('Ошибка обработки. Попробуйте ещё раз.', 'Emal xətası. Yenidən cəhd edin.', 'Processing failed. Please retry.')}, status=503)
    finally:
        cache.delete(key)


@never_cache
@require_POST
def save_owner_photos(request, pk=None):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'errors': {'__all__': [t('Войдите в аккаунт.', 'Hesaba daxil olun.', 'Please sign in.')]}}, status=403)
    try:
        request_id = str(UUID(request.POST.get('photo_request_id', '')))
    except ValueError:
        return JsonResponse({'ok': False, 'errors': {'__all__': ['Invalid request ID']}}, status=400)
    key = 'photo-save:' + hashlib.sha256(f'{request.user.pk}:{pk}:{request_id}'.encode()).hexdigest()
    cached = cache.get(key)
    if isinstance(cached, dict):
        return JsonResponse(cached)
    if not cache.add(key, 'saving', timeout=300):
        return JsonResponse({'ok': False, 'errors': {'__all__': [t('Сохранение ещё выполняется. Повторите через несколько секунд.', 'Saxlama davam edir. Bir neçə saniyədən sonra təkrarlayın.', 'Still saving. Retry in a few seconds.')]}}, status=409)
    success = False
    try:
        if sum(file.size for _, files in request.FILES.lists() for file in files) > MAX_IMAGE_BATCH_BYTES:
            return JsonResponse({'ok': False, 'errors': {'gallery_images': [t('Общий размер фото — до 22 МБ.', 'Şəkillərin ümumi ölçüsü 22 MB-dəkdir.', 'Photos must total at most 22 MB.')]}}, status=422)
        data = request.POST.copy()
        data.update(is_temporary='', temporary_start='', temporary_end='')
        action = data.get('form_action', 'save_draft')
        if action not in {'save_draft', 'save_and_publish'}:
            return JsonResponse({'ok': False, 'errors': {'__all__': ['Invalid action']}}, status=400)
        controller = OwnerPlacesController.build_default()
        if pk is None:
            result = controller.create_place(request=request, data=data, files=request.FILES, draft_save_only=action == 'save_draft')
        else:
            result = controller.save_edit_form(request=request, place_id=pk, data=data, files=request.FILES, draft_save_only=action == 'save_draft', submit_for_moderation=action == 'save_and_publish')
        if not result.ok:
            errors = {name: [str(error) for error in values] for name, values in result.form.errors.items()} if result.form is not None else {'__all__': [str(result.message)]}
            return JsonResponse({'ok': False, 'errors': errors}, status=422 if result.form is not None else 403)
        url = reverse('owner_place_edit', args=[result.place.pk]) + '#photos' if action == 'save_draft' else reverse('owner_places_dashboard')
        payload = {'ok': True, 'redirect': url}
        cache.set(key, payload, timeout=86400)
        success = True
        return JsonResponse(payload)
    finally:
        if not success:
            cache.delete(key)
