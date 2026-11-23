"""Admin transport over the same receipts and actual actor, never impersonation."""
from django.contrib import admin
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from catalog.models import Organization, OrganizationConnectionOperation
from catalog.controllers.organization_workspace import CONNECTION_LABELS, connection_context, connection_request
from catalog.services import organization_connections as service, organization_ownership

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


def _can_use_informational_link(user):
    try:
        organization_ownership._reviewer(user)
    except PermissionDenied:
        return False
    return True


def _organization_selection(model_admin, request, context, organization):
    params = request.POST if request.method == 'POST' else request.GET
    selected = [] if params.get('action') == 'clear' else [int(value) for value in params.getlist('place_ids')]
    if selected:
        selected = _visible_ids(model_admin, request, service._ids(selected))
    can_information = _can_use_informational_link(request.user)
    kind = params.get('relationship_kind', '' if can_information else 'business')
    if kind not in ('', 'business', 'informational'):
        raise ValidationError('Unsupported relationship kind.')
    if kind == 'informational' and not can_information:
        raise PermissionDenied

    preview_requested = request.method == 'POST' and params.get('action') == 'preview'
    if preview_requested and kind:
        operation = service.preview_connections(actor=request.user, organization_id=organization.pk,
            relationship_kind=kind, place_ids=selected)
        context.update(connection_context(request, operation))
        context['edit_selection_url'] = reverse('admin:catalog_place_organization_connections', query={
            'organization_id': organization.pk, 'place_ids': selected, 'relationship_kind': kind, 'q': params.get('q', ''),
        })
        return

    query = params.get('q', '')
    found = service.search_places(actor=request.user, organization_id=organization.pk, query=query,
        cursor=params.get('cursor', 0), relationship_kind=kind or 'business', place_scope=model_admin.get_queryset(request))
    for row in found['rows']:
        row['message'] = _('Подключится после подтверждения') if row['code'] == 'connected' else CONNECTION_LABELS[row['code']]
        row['selected'] = row['id'] in selected
    page_ids = {row['id'] for row in found['rows']}
    context.update(found, query=query, search=True, selection_count=len(selected), can_information=can_information,
        relationship_kind=kind, carried=[pk for pk in selected if pk not in page_ids],
        connection_kind_required=preview_requested and not kind)


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
    back_url = reverse('admin:catalog_place_changelist')
    context={**model_admin.admin_site.each_context(request),'base_template':'admin/base_site.html',
        'admin_mode':True,'back_url':back_url,'admin_pick_url':back_url,'connection_url':request.path}
    try:
        organization_id = request.GET.get('organization_id')
        organization = None
        if organization_id:
            organization = Organization.objects.get(pk=int(organization_id), archived_at__isnull=True)
            if not _target_visible(model_admin, request, organization):
                raise PermissionDenied
            pick_url = reverse('admin:catalog_place_organization_connections', query={'organization_id': organization.pk})
            context.update(organization=organization, admin_pick=True,
                connection_organization_name=service.organization_name(organization),
                connection_url=pick_url, admin_pick_url=pick_url)
            org_admin = model_admin.admin_site._registry.get(Organization)
            if org_admin and org_admin.has_view_permission(request, organization):
                context['organization_card_url'] = reverse('admin:catalog_organization_change', args=[organization.pk])
        if request.method=='POST' and request.POST.get('connection_selection')=='1':
            ids=service._ids([int(pk) for pk in request.POST.getlist('_selected_action')])
            _visible_ids(model_admin,request,ids)
            return connect_to_organization(model_admin,request,model_admin.get_queryset(request).filter(pk__in=ids))
        if request.method=='POST' and request.POST.get('action') in ('confirm','resume') and not request.POST.get('selection'):
            operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(request.POST.get('preview_id')),actor=request.user,action='connect')
            _visible_ids(model_admin,request,list(operation.items.values_list('place_id',flat=True)))
            operation=connection_request(request,org_id=organization.pk if organization else None,operation=operation,expected_action='connect')
            receipt_query = {'operation': operation.pk}
            if organization:
                receipt_query['organization_id'] = organization.pk
            return redirect(reverse('admin:catalog_place_organization_connections', query=receipt_query))
        operation_id=request.GET.get('operation')
        if operation_id:
            operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(operation_id),actor=request.user)
            if organization and operation.organization_id != organization.pk:
                raise PermissionDenied
            context.update(connection_context(request,operation))
        elif organization:
            _organization_selection(model_admin, request, context, organization)
            if context.get('connection_kind_required'):
                return render(request, 'admin/catalog/place/organization_connections.html', context, status=400)
        else:
            token=request.POST.get('selection') or request.GET.get('selection','')
            selected=signing.loads(token,salt=SALT,max_age=600)
            if selected.get('actor')!=request.user.pk: raise PermissionDenied
            ids=service._ids(selected['ids']);_visible_ids(model_admin,request,ids)
            context['selection']=token
            relationship_kind = request.POST.get('relationship_kind', '')
            if request.method == 'GET' or (
                request.POST.get('action') == 'preview' and relationship_kind not in {'business', 'informational'}
            ):
                targets = [
                    org for org in Organization.objects.filter(archived_at__isnull=True).order_by('name_az', 'pk')
                    if _target_visible(model_admin, request, org)
                ]
                for target in targets:
                    target.connection_display_name = service.organization_name(target)
                context.update(admin_select=True, selected_count=len(ids), targets=targets,
                               can_information=_can_use_informational_link(request.user))
                if request.method == 'POST':
                    context.update(connection_kind_required=True,
                                   selected_organization_id=request.POST.get('organization_id', ''))
                    return render(request, 'admin/catalog/place/organization_connections.html', context, status=400)
            if request.method=='POST':
                if request.POST.get('action')=='confirm':
                    operation=OrganizationConnectionOperation.objects.get(pk=service._uuid(request.POST.get('preview_id')),actor=request.user)
                    if list(operation.items.order_by('place_id').values_list('place_id',flat=True))!=ids: raise PermissionDenied
                    operation=connection_request(request,operation=operation,expected_action='connect')
                    return redirect(reverse('admin:catalog_place_organization_connections')+'?operation='+str(operation.pk))
                org=Organization.objects.get(pk=int(request.POST.get('organization_id','0')),archived_at__isnull=True)
                if not _target_visible(model_admin,request,org): raise PermissionDenied
                operation=service.preview_connections(actor=request.user,organization_id=org.pk,
                    relationship_kind=relationship_kind,place_ids=ids)
                context.update(connection_context(request,operation))
    except (ObjectDoesNotExist,PermissionDenied):raise Http404
    except (ValueError,KeyError,signing.BadSignature,ValidationError):
        context['connection_error']=_('Не удалось подтвердить. Проверьте выбор, согласие и срок просмотра. Обновите просмотр перед новым действием.')
        return render(request,'admin/catalog/place/organization_connections.html',context,status=400)
    return render(request,'admin/catalog/place/organization_connections.html',context)
