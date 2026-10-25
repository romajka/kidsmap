"""Private current-form preview. POST only: no public draft token or URL sharing."""
import copy
from django.contrib import admin as django_admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from catalog.models import Place, PlacePhoto
from catalog.services.place_access import has_place_permission
from catalog.services.place_editor_preview import build_editor_preview
from catalog.services.admin_site_preview import render_site_preview


@never_cache
@csrf_protect
@require_POST
def place_editor_preview(request, pk=None):
    if not request.user.is_authenticated or not request.user.is_active:
        raise PermissionDenied
    request.site_preview = True
    admin_surface = request.GET.get('surface') == 'admin'
    volunteer_surface = request.GET.get('surface') == 'volunteer'
    place = None
    if volunteer_surface:
        from catalog.services.staff_roles import can_use_volunteer_workspace
        from catalog.services.volunteer_places import own_places
        if not can_use_volunteer_workspace(request.user): raise PermissionDenied
        if pk is not None: place = get_object_or_404(own_places(request.user), pk=pk)
    elif admin_surface:
        model_admin = django_admin.site._registry[Place]
        if pk is not None: place = get_object_or_404(model_admin.get_queryset(request), pk=pk)
        permitted = model_admin.has_change_permission(request, place) if place else model_admin.has_add_permission(request)
        if not request.user.is_staff or not permitted: raise PermissionDenied
    elif pk is not None:
        place = get_object_or_404(Place, pk=pk, deleted_at__isnull=True)
        if not has_place_permission(user=request.user,place=place,permission_code='place.edit'):
            raise PermissionDenied
    else:
        from catalog.services.owner_place_use_cases import ensure_owner_permission
        if not ensure_owner_permission(user=request.user).ok: raise PermissionDenied
    language = request.POST.get('_km_preview_language') or getattr(request, 'LANGUAGE_CODE', 'az')
    language = language if language in ('az','ru','en') else 'az'
    data = request.POST.copy()
    check_only = data.get('_km_check_required') == '1'
    source = copy.copy(place) if place else Place()
    if place:
        source._state = copy.copy(place._state);source._state.fields_cache = {}
    if volunteer_surface:
        from catalog.services.volunteer_places import editor_form
        from catalog.models import VolunteerPlaceRevision
        revision = VolunteerPlaceRevision.objects.filter(place=place).first() if place else None
        data['action'] = 'draft'
        source.created_by = request.user
        form = editor_form(source, revision, data=data, files=request.FILES)
        # Preview does not save/version a candidate. Completeness still uses
        # the canonical publication verdict below; values retain validation.
        for field in form.fields.values(): field.required = False
    elif admin_surface:
        from catalog.domain_admin.place import PlaceAdminForm
        if check_only:
            data.pop('_save_draft',None);data['status']='published';data['is_active']='1'
        else:
            data['_save_draft'] = '1'
        form = PlaceAdminForm(data=data,files=request.FILES,instance=source)
        # The base form includes platform-only fields omitted from the custom UI.
        for field in form.fields.values(): field.required = False
        form.location_actor=request.user
    else:
        from catalog.forms import OwnerPlaceEditForm
        form = OwnerPlaceEditForm(data=data,files=request.FILES,instance=source,draft_save_only=not check_only,submit_for_moderation=check_only)
    back = reverse('admin:volunteer_edit',args=[pk]) if volunteer_surface and pk else reverse('admin:volunteer_add') if volunteer_surface else reverse('admin:catalog_place_change',args=[pk]) if admin_surface and pk else reverse('admin:catalog_place_add')+'?type=permanent' if admin_surface else reverse('owner_place_edit',args=[pk]) if pk else reverse('owner_place_create')+'?type=permanent'
    valid = form.is_valid()
    from catalog.services.image_uploads import MAX_IMAGE_BATCH_BYTES
    if sum(file.size for _, uploads in request.FILES.lists() for file in uploads) > MAX_IMAGE_BATCH_BYTES:
        from catalog.services.permanent_place_rules import copy as t
        form.add_error('photo',t('Общий размер фото — до 22 МБ.','Şəkillərin ümumi ölçüsü 22 MB-dəkdir.','Photos must total at most 22 MB.'));valid=False
    if admin_surface:
        for formset_class, inline in model_admin.get_formsets_with_inlines(request,place):
            if inline.model is not PlacePhoto: continue
            prefix=formset_class.get_default_prefix()
            if prefix+'-TOTAL_FORMS' not in data: continue
            formset=formset_class(data=data,files=request.FILES,instance=source,prefix=prefix)
            if not formset.is_valid():
                messages=list(formset.non_form_errors())
                for row in formset.forms:
                    for errors in row.errors.values(): messages.extend(errors)
                form.add_error('photo',messages);valid=False
            else:
                form.preview_gallery_forms=formset.forms
    if check_only:
        # Existing live cards deliberately permit incomplete ordinary edits.
        # A completeness check must still report the authoritative missing data.
        readiness=getattr(form,'place_readiness',None)
        if admin_surface and readiness:
            for issue in readiness.issues:
                name=issue.field if issue.field in form.fields else None
                if (name or '__all__') not in form.errors: form.add_error(name,str(issue.message))
            valid=not form.errors
        from catalog.services.place_editor_readiness import editor_readiness
        progress = editor_readiness(form)
        if volunteer_surface:
            for item in progress['items']:
                if not item['complete']:
                    name = item['field'] if item['field'] in form.fields else None
                    if (name or '__all__') not in form.errors: form.add_error(name, item['message'])
            valid = not form.errors
            progress['is_ready'] = progress['is_ready'] and valid
        response=JsonResponse({'ok':valid,'errors':form.editor_errors,'error_targets':form.editor_error_targets,'readiness':progress},status=200 if valid else 422)
        response['X-Robots-Tag']='noindex, nofollow, noarchive'
        response['Cache-Control']='private, no-store, max-age=0'
        return response
    if valid:
        try:
            preview = build_editor_preview(form,place=place,admin=admin_surface,files=request.FILES,post=data)
            response = render_site_preview(request,preview,language=language,back_url=back)
        except ValidationError as error:
            errors=error.message_dict if hasattr(error,'error_dict') else {'gallery_images':error.messages}
            for name, messages in errors.items(): form.add_error(name if name in form.fields else None,messages)
            response = render(request,'pages/place_editor_preview_errors.html',{'form':form,'back_url':back},status=422)
    else:
        response = render(request,'pages/place_editor_preview_errors.html',{'form':form,'back_url':back},status=422)
    response['X-Robots-Tag']='noindex, nofollow, noarchive'
    response['Cache-Control']='private, no-store, max-age=0'
    return response
