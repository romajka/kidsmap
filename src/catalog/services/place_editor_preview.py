"""In-memory preview of the validated current form. Never persist uploaded files."""
import base64
import copy
from types import SimpleNamespace
from django.core.exceptions import ValidationError
from catalog.models import Place, PlacePhoto
from catalog.services import publication
from catalog.services.photo_gallery import gallery_key


def _image(file, index):
    """Only normalized image bytes enter a data URL, never an arbitrary upload."""
    from catalog.services.image_uploads import normalize_uploaded_image
    normalized = normalize_uploaded_image(file)
    normalized.seek(0)
    content = normalized.read()
    normalized.seek(0)
    # Image normalization emits a known web image format, not the submitted MIME.
    mime = 'image/png' if content.startswith(b'\x89PNG') else 'image/webp' if content[:4] == b'RIFF' else 'image/jpeg'
    return SimpleNamespace(name=f'editor-preview-{index}', url=f'data:{mime};base64,'+base64.b64encode(content).decode('ascii'),
        storage=SimpleNamespace(exists=lambda name: True))


def build_editor_preview(form, *, place=None, admin=False, files=None, post=None):
    """The caller has checked ACL and form validity. No save helper is called."""
    candidate = form.instance
    data = publication.snapshot(candidate, 'place')
    if not candidate.category_id:
        from catalog.models import Category
        from django.utils.translation import gettext
        candidate.category = Category(code='',name=gettext('Категория не выбрана'))
    for name in ('pricing_plans', 'nested_pricing'):
        value = form.cleaned_data.get(name)
        if value is not None:
            data[name] = value
    if getattr(form, 'cleaned_schedule_days', None) is not None:
        data['structured_schedule'] = form.cleaned_schedule_days
    from catalog.services.publication_forms import gallery_for_edit
    gallery = copy.deepcopy((getattr(form, '_saved_gallery', None) or gallery_for_edit(place)) if place else [])
    deleted = {str(value) for value in form.cleaned_data.get('delete_gallery_ids') or []}
    images = []
    if candidate.photo and not getattr(candidate.photo,'_committed',True):
        images.append(_image(candidate.photo.file, 'main'))
    elif candidate.photo:
        images.append(candidate.photo)
    elif candidate.cover_photo:
        images.append(candidate.cover_photo)
    main_count=len(images)
    gallery_images=[]
    if admin and hasattr(form,'preview_gallery_forms'):
        allowed_ids={row['id'] for row in gallery if row.get('id') is not None}
        for index,row_form in enumerate(form.preview_gallery_forms):
            cleaned=row_form.cleaned_data
            if not cleaned or cleaned.get('DELETE'): continue
            original=cleaned.get('id')
            if original and original.pk not in allowed_ids:
                raise ValidationError({'photo':'Галерея изменилась. Обновите страницу.'})
            image=row_form.instance.image
            if not image: continue
            if not getattr(image,'_committed',True):image=_image(image.file,f'inline-{index}')
            gallery_images.append((cleaned.get('order') or 0,index,image))
        images.extend(image for order,index,image in sorted(gallery_images,key=lambda row:row[:2]))
    else:
        positions={str(key):index for index,key in enumerate(form.cleaned_data.get('gallery_order') or [])}
        for index,row in enumerate(gallery):
            if str(row.get('id')) in deleted or gallery_key(row) in deleted: continue
            image=PlacePhoto(image=row['image']).image
            gallery_images.append((positions.get(gallery_key(row),row.get('order',index)),index,image))
    uploads = files.getlist('gallery_uploads') if admin and files else form.cleaned_data.get('gallery_images') or []
    from catalog.services.image_uploads import MAX_GALLERY_IMAGES
    if len(images) + len(uploads) > MAX_GALLERY_IMAGES + 1:
        raise ValidationError({'gallery_images':'Слишком много фотографий для предпросмотра.'})
    if admin:
        if not hasattr(form,'preview_gallery_forms'):
            images.extend(image for order,index,image in sorted(gallery_images,key=lambda row:row[:2]))
        images.extend(_image(file,index) for index,file in enumerate(uploads))
    else:
        for index,file in enumerate(uploads):
            gallery_images.append((positions.get(f'new:{index}',len(gallery)+index),len(gallery)+index,_image(file,index)))
        images.extend(image for order,index,image in sorted(gallery_images,key=lambda row:row[:2]))
    if len(images)-main_count > MAX_GALLERY_IMAGES:
        raise ValidationError({'photo':'Слишком много фотографий для предпросмотра.'})
    # No persisted relations can belong to a new form. The transient positive ID
    # is used only to construct public-template URLs; relation queries use None.
    new = not candidate.pk
    if new:
        candidate.pk = 10**9
        candidate.slug = candidate.slug or 'editor-preview'
    live = place or copy.copy(candidate)
    return {'candidate':candidate, 'place':live, 'snapshot':data, 'show_submission':False,
        'stale':False, 'submitted_fields':frozenset({'pricing_plans','nested_pricing','structured_schedule'}),
        'editor_images':images, 'editor_new':new, 'editor_current':True}
