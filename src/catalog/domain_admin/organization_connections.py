"""Admin transport over the same receipts and actual actor, never impersonation."""
from django.contrib import admin
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from catalog.models import Organization, OrganizationConnectionOperation
from catalog.controllers.organization_workspace import connection_context, connection_request
from catalog.services import organization_connections as service, organization_ownership
from catalog.services.staff_roles import is_volunteer

SALT='catalog.organization.connection.selection'


def _gate(model_admin, request):
    if not model_admin.has_connection_permission(request): raise Http404


def _target_visible(model_admin,request,org):
    org_admin=model_admin.admin_site._registry.get(Organization)
    return service.organization_visible(request.user,org) or bool(org_admin and org_admin.has_view_permission(request,org))


def _visible_ids(model_admin,request,ids):
    selected=list(model_admin.get_queryset(request).filter(pk__in=ids))
    if len(selected)!=len(ids) or any(not model_admin.has_view_permission(request,p) for p in selected): raise PermissionDenied
    return ids


@admin.action(description=_('Подключить к организации'), permissions=['connection'])
def connect_to_organization(model_admin,request,queryset):
    _gate(model_admin,request)
    ids=list(queryset.order_by('pk').values_list('pk',flat=True)[:101])
    try: service._ids(ids);_visible_ids(model_admin,request,ids)
    except (ValidationError,PermissionDenied):
        model_admin.message_user(request,_('Выберите от 1 до 100 доступных мест.'),level='error')
        return redirect('admin:catalog_place_changelist')
    token=signing.dumps({'actor':request.user.pk,'ids':ids},salt=SALT,compress=True)
    from urllib.parse import urlencode
    return redirect(reverse('admin:catalog_place_organization_connections')+'?'+urlencode({'selection':token}))


def organization_connections_view(model_admin,request):
    _gate(model_admin,request)
    context={**model_admin.admin_site.each_context(request),'base_template':'admin/base_site.html',
        'admin_mode':True,'back_url':reverse('admin:catalog_place_changelist'),'connection_url':request.path}
    try:
        if request.method=='POST' and request.POST.get('connection_selection')=='1':
            ids=service._ids([int(pk) for pk in request.POST.getlist('_selected_action')])
            _visible_ids(model_admin,request,ids)
            return connect_to_organization(model_admin,request,model_admin.get_queryset(request).filter(pk__in=ids))
        if request.method=='POST' and request.POST.get('action') in ('confirm','resume') and not request.POST.get('selection'):
            operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(request.POST.get('preview_id')),actor=request.user,action='connect')
            _visible_ids(model_admin,request,list(operation.items.values_list('place_id',flat=True)))
            operation=connection_request(request,operation=operation,expected_action='connect')
            return redirect(reverse('admin:catalog_place_organization_connections')+'?operation='+str(operation.pk))
        operation_id=request.GET.get('operation')
        if operation_id:
            operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(operation_id),actor=request.user)
            context.update(connection_context(request,operation))
        else:
            token=request.POST.get('selection') or request.GET.get('selection','')
            selected=signing.loads(token,salt=SALT,max_age=600)
            if selected.get('actor')!=request.user.pk: raise PermissionDenied
            ids=service._ids(selected['ids']);_visible_ids(model_admin,request,ids)
            context['selection']=token
            if request.method=='POST':
                if request.POST.get('action')=='confirm':
                    operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(request.POST.get('preview_id')),actor=request.user)
                    if list(operation.items.order_by('place_id').values_list('place_id',flat=True))!=ids: raise PermissionDenied
                    operation=connection_request(request,operation=operation,expected_action='connect')
                    return redirect(reverse('admin:catalog_place_organization_connections')+'?operation='+str(operation.pk))
                org=Organization.objects.get(pk=int(request.POST.get('organization_id','0')),archived_at__isnull=True)
                if not _target_visible(model_admin,request,org): raise PermissionDenied
                operation=service.preview_connections(actor=request.user,organization_id=org.pk,
                    relationship_kind=request.POST.get('relationship_kind','business'),place_ids=ids)
                context.update(connection_context(request,operation))
            else:
                targets=[o for o in Organization.objects.filter(archived_at__isnull=True).order_by('name_az','pk') if _target_visible(model_admin,request,o)]
                for target in targets:target.connection_display_name=service.organization_name(target)
                try:organization_ownership._reviewer(request.user);can_information=True
                except PermissionDenied:can_information=False
                context.update(admin_select=True,selected_count=len(ids),targets=targets,can_information=can_information)
    except (ObjectDoesNotExist,PermissionDenied):raise Http404
    except (ValueError,KeyError,signing.BadSignature,ValidationError):
        context['connection_error']=_('Не удалось подтвердить. Проверьте выбор, согласие и срок просмотра. Обновите просмотр перед новым действием.')
        return render(request,'admin/catalog/place/organization_connections.html',context,status=400)
    return render(request,'admin/catalog/place/organization_connections.html',context)
