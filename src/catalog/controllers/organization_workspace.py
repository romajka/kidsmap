"""Owner organization screens. Domain services remain the only mutation/ACL authority."""
from django import forms
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import Http404
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from catalog.models import Category, Organization, OrganizationPlaceRequest, Place, Program, ServerDraft
from catalog.services import business_team, organization_ownership, publication
from django.utils.translation import gettext_lazy as _
import uuid
from catalog.services import organization_connections as connections


CONNECTION_LABELS = {
    'connected': _('Подключение подтверждено'), 'requested': _('Запрос: нужно согласие второго владельца'),
    'waiting_owner': _('Ожидает второго владельца'), 'already_connected': _('Уже подключено'),
    'detached': _('Отсоединение подтверждено'), 'already_detached': _('Уже отсоединено'),
    'other_network': _('Другая организация: пропустим, перенос требует отвязки'),
    'kind_conflict': _('Другой тип связи: нужна отдельная проверка'), 'no_rights': _('Нет прав владельца стороны'),
    'owner_required': _('Нужны владельцы места и организации'), 'changed': _('Данные изменились: проверьте заново'),
    'archived': _('Организация архивирована'), 'program_conflict': _('Занятия связаны с программой другой сети'),
    'manual_review': _('Нужна ручная проверка запроса или программы'),
    'unavailable': _('Карточка недоступна'), 'failed': _('Ошибка: строка не изменена'),
}


def connection_context(request, operation):
    result = connections.connection_result(actor=request.user, operation_id=operation.pk)
    for row in result['rows']:
        row['message'] = CONNECTION_LABELS[row['code']]
        if operation.status=='preview' and row['code']=='connected': row['message']=_('Подключится после подтверждения')
        if operation.status=='preview' and row['code']=='detached': row['message']=_('Отсоединится после подтверждения')
        if operation.status=='preview' and row['code']=='requested': row['message']=_('Будет отправлен запрос второму владельцу')
        if row.get('complete') and row['code']=='requested': row['message']=_('Запрос создан этой операцией')
        if row.get('complete') and row['code']=='connected': row['message']=_('Подключено этой операцией')
    result['summary'] = {
        'immediate':sum(row['code'] in ('connected','detached') for row in result['rows']),
        'requests':sum(row['code'] in ('requested','waiting_owner') for row in result['rows']),
        'unchanged':sum(row['code'] in ('already_connected','already_detached') for row in result['rows']),
        'blocked':sum(row['code'] not in connections.EXECUTABLE for row in result['rows']),
    }
    return {'operation': operation, 'result': result, 'rows': result['rows'],
        'review': operation.status == 'preview', 'idempotency_key': operation.idempotency_key or uuid.uuid4()}


def organization_connection_target(request):
    if not request.user.is_authenticated:return _login(request)
    ids=request.GET.getlist('place_ids')
    try:
        if request.GET.get('organization_id'):
            org=Organization.objects.get(pk=int(request.GET['organization_id']),archived_at__isnull=True)
            if not connections.organization_visible(request.user,org):raise PermissionDenied
            from urllib.parse import urlencode
            return redirect(reverse('organization_connections',args=[org.pk])+'?'+urlencode({'place_ids':ids},doseq=True))
        targets=[org for org in Organization.objects.filter(archived_at__isnull=True).filter(Q(status='published')|Q(owner=request.user)).order_by('name_az','pk') if connections.organization_visible(request.user,org)]
    except (ValueError,ObjectDoesNotExist,PermissionDenied):raise Http404
    for target in targets: target.connection_display_name=connections.organization_name(target)
    return render(request,'pages/organization_connections.html',{'target_select':True,'targets':targets,'selected':ids})


def connection_request(request, *, org_id=None, operation=None, detach_place=None, expected_action=None):
    """Shared transport; target/mode come from the server-held receipt at confirm."""
    if request.method == 'POST' and request.POST.get('action') in ('confirm','resume'):
        from catalog.models import OrganizationConnectionOperation
        operation = OrganizationConnectionOperation.objects.get(pk=connections._uuid(request.POST.get('preview_id')))
        if operation.actor_id != request.user.pk or (org_id is not None and operation.organization_id != org_id):
            raise PermissionDenied
        if expected_action is not None and operation.action != expected_action: raise PermissionDenied
        if detach_place is not None and (operation.action != 'detach' or not operation.items.filter(place_id=detach_place).exists()):
            raise PermissionDenied
        if request.POST.get('consent') != '1':
            raise ValidationError(_('Подтвердите последствия операции.'), code='consent')
        execute = connections.execute_detach if operation.action == 'detach' else connections.execute_connections
        return execute(actor=request.user, preview_id=operation.pk, idempotency_key=request.POST.get('idempotency_key'))
    return operation


def organization_connections(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = Organization.objects.filter(pk=org_id).first()
    if org is None: raise Http404
    # Place owners can consent without receiving private organization workspace access.
    if not connections.organization_visible(request.user,org) and org.owner_id != request.user.pk and not Place.objects.filter(owner=request.user,organization_requests__organization=org).exists():
        # Also allow a visible place-side owner to choose a published network; private targets stay private.
        raise Http404
    context = {'organization': org if connections.organization_visible(request.user,org) else None,
        'connection_organization_name':connections.organization_name(org) if connections.organization_visible(request.user,org) else None,
        'org_id':org.pk, 'connection_url':request.path}
    try:
        operation = connection_request(request,org_id=org.pk,expected_action='connect')
        if operation: return redirect('organization_connection_result',operation_id=operation.pk)
        if request.method == 'POST' and request.POST.get('action')=='preview':
            ids=[int(value) for value in request.POST.getlist('place_ids')]
            operation=connections.preview_connections(actor=request.user,organization_id=org.pk,
                relationship_kind='business',place_ids=ids)
            context.update(connection_context(request,operation))
        else:
            params=request.POST if request.method=='POST' else request.GET
            selected=[int(value) for value in params.getlist('place_ids')]
            if len(selected)>100 or len(set(selected)) != len(selected): raise ValidationError(_('Выберите от 1 до 100 мест.'))
            found=connections.search_places(actor=request.user,organization_id=org.pk,query=params.get('q',''),cursor=params.get('cursor',0))
            for row in found['rows']:
                row['message']=_('Подключится после подтверждения') if row['code']=='connected' else CONNECTION_LABELS[row['code']];row['selected']=row['id'] in selected
            page_ids={row['id'] for row in found['rows']}
            context.update(found,query=params.get('q',''),selected=selected,
                carried=[pk for pk in selected if pk not in page_ids],selection_count=len(selected),search=True)
    except PermissionDenied: raise Http404
    except ObjectDoesNotExist: raise Http404
    except (ValidationError,ValueError) as exc:
        context['connection_error']=_('Не удалось подтвердить. Проверьте выбор, согласие и срок просмотра. Обновите просмотр перед новым действием.')
        return render(request,'pages/organization_connections.html',context,status=400)
    return render(request,'pages/organization_connections.html',context)


def organization_connection_result(request, operation_id):
    if not request.user.is_authenticated: return _login(request)
    from catalog.models import OrganizationConnectionOperation
    try:
        operation=OrganizationConnectionOperation.objects.get(pk=operation_id,actor=request.user)
        if request.method=='POST':
            if request.POST.get('preview_id') != str(operation.pk): raise PermissionDenied
            operation=connection_request(request,operation=operation)
            return redirect('organization_connection_result',operation_id=operation.pk)
        context=connection_context(request,operation)
        context.update(connection_url=request.path,org_id=operation.organization_id)
    except (ObjectDoesNotExist,PermissionDenied): raise Http404
    except ValidationError:
        context=connection_context(request,operation)
        context['connection_error']=_('Операция не подтверждена. Обновите просмотр и повторите.')
        return render(request,'pages/organization_connections.html',context,status=409)
    return render(request,'pages/organization_connections.html',context)


def organization_detach_preview(request,org_id,place_id):
    if not request.user.is_authenticated: return _login(request)
    try:
        if request.method=='POST':
            operation=connection_request(request,org_id=org_id,detach_place=place_id)
            if operation: return redirect('organization_connection_result',operation_id=operation.pk)
        operation=connections.preview_detach(actor=request.user,place_id=place_id,organization_id=org_id)
        context=connection_context(request,operation)
        context.update(connection_url=request.path,org_id=org_id)
    except (ObjectDoesNotExist,PermissionDenied): raise Http404
    except ValidationError:
        return render(request,'pages/organization_detach.html',{'connection_error':_('Операция не подтверждена. Обновите просмотр и повторите.')},status=409)
    return render(request,'pages/organization_detach.html',context)


def _organization_form_labels(form):
    for language in ('az', 'ru', 'en'):
        form.fields['name_' + language].label = _('Название организации (%(language)s)') % {'language': language.upper()}
    form.fields['description_az'].label = _('Описание организации (%(language)s)') % {'language': 'AZ'}
    for name, label in {'phone': _('Телефон'), 'whatsapp': 'WhatsApp', 'website': _('Сайт организации'),
                        'allow_separate': _('Создать отдельную организацию'),
                        'expected_version': _('Версия карточки'), 'revision_version': _('Версия изменений'),
                        'submit': _('Отправить на проверку')}.items():
        if name in form.fields:
            form.fields[name].label = label


class OrganizationCreateForm(forms.Form):
    name_az = forms.CharField(max_length=255)
    name_ru = forms.CharField(max_length=255, required=False)
    name_en = forms.CharField(max_length=255, required=False)
    description_az = forms.CharField(required=False, widget=forms.Textarea)
    phone = forms.CharField(max_length=50, required=False)
    whatsapp = forms.CharField(max_length=50, required=False)
    website = forms.URLField(required=False)
    allow_separate = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _organization_form_labels(self)


class BranchCreateForm(forms.Form):
    name_az = forms.CharField(max_length=255)
    category_id = forms.ModelChoiceField(queryset=Category.objects.all())
    allow_separate = forms.BooleanField(required=False)


class OrganizationCandidateForm(forms.Form):
    name_az = forms.CharField(max_length=255, required=False)
    name_ru = forms.CharField(max_length=255, required=False)
    name_en = forms.CharField(max_length=255, required=False)
    description_az = forms.CharField(required=False, widget=forms.Textarea)
    phone = forms.CharField(max_length=50, required=False)
    whatsapp = forms.CharField(max_length=50, required=False)
    website = forms.URLField(required=False)
    expected_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    revision_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    submit = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _organization_form_labels(self)


ORGANIZATION_CONFLICT_COPY = {
    'candidate_version_conflict': _('Изменения уже сохранены в другой вкладке или другим редактором. Ваш ввод остался в форме. Скопируйте нужный текст и сравните его с актуальными данными перед повторной отправкой.'),
    'publication_source_conflict': _('Данные организации изменились после открытия формы. Ваш ввод остался в форме. Скопируйте нужный текст и сравните его с актуальными данными перед повторной отправкой.'),
    'candidate_source_conflict': _('Данные организации изменились после открытия формы. Ваш ввод остался в форме. Скопируйте нужный текст и сравните его с актуальными данными перед повторной отправкой.'),
    'publication_schema_conflict': _('Форма устарела. Ваш ввод остался в форме. Скопируйте нужный текст, откройте актуальные данные и проверьте их перед повторной отправкой.'),
    'candidate_dependency_conflict': _('Связанные данные организации изменились. Ваш ввод остался в форме. Скопируйте нужный текст и сравните его с актуальными данными перед повторной отправкой.'),
}


def _organization_save_errors(form, exc):
    errors = exc.error_list if isinstance(exc, ValidationError) and hasattr(exc, 'error_list') else [exc]
    for error in errors:
        code = getattr(error, 'code', None)
        message = ORGANIZATION_CONFLICT_COPY.get(code, _('Не удалось отправить изменения. Ваш ввод остался в форме. Проверьте данные и повторите отправку.'))
        form.add_error(None, ValidationError(message, code=code))
        if code in ORGANIZATION_CONFLICT_COPY:
            form.version_conflict = True


def _login(request):
    from django.contrib.auth.views import redirect_to_login
    return redirect_to_login(request.get_full_path(), reverse('account_login'))


def _organization(request, org_id, action='organization.view'):
    org = Organization.objects.filter(pk=org_id, archived_at__isnull=True).first()
    if org is None or not business_team.has_action(user=request.user, target=org, action=action):
        raise Http404
    return org


def _owned_and_accessible_orgs(user):
    candidates = Organization.objects.filter(archived_at__isnull=True).filter(
        Q(owner=user) |
        Q(team_grants__member=user, team_grants__is_active=True)
    ).distinct().order_by('pk')
    return [o for o in candidates if business_team.has_action(user=user, target=o, action='organization.view')]


def _standalone_places(user):
    ids = business_team.accessible_place_ids(user=user, action='place.view')
    return list(Place.objects.filter(pk__in=ids, organization__isnull=True, deleted_at__isnull=True).order_by('pk'))


def organization_index(request):
    if not request.user.is_authenticated: return _login(request)
    return render(request, 'pages/organization_workspace.html', {
        'organizations': _owned_and_accessible_orgs(request.user),
        'standalone_places': _standalone_places(request.user),
        'create_form': OrganizationCreateForm(),
        'workspace_mode': 'index',
    })


def organization_create(request):
    if not request.user.is_authenticated: return _login(request)
    duplicate_detected = False
    if request.method == 'POST':
        form = OrganizationCreateForm(request.POST)
        if form.is_valid():
            values = {k: v for k, v in form.cleaned_data.items() if k != 'allow_separate' and v}
            try:
                org = organization_ownership.create_organization(actor=request.user, values=values,
                    allow_separate=form.cleaned_data['allow_separate'])
                # A nonce carries no form data in the URL and only acknowledges this successful POST.
                token = uuid.uuid4().hex
                request.session['organization_create_confirmation'] = {
                    'token': token, 'organization_id': org.pk, 'actor_id': request.user.pk,
                    'fields': {name: request.POST.get(name, '') for name in form.fields if name != 'allow_separate'},
                }
                return redirect(reverse('organization_workspace_detail', args=[org.pk]) + '?created=' + token)
            except PermissionDenied: raise Http404
            except ValidationError as exc:
                if getattr(exc, 'code', None) == 'possible_duplicate' or 'possible_duplicate' in str(exc):
                    duplicate_detected = True
                form.add_error(None, exc)
        return render(request, 'pages/organization_create.html', {
            'create_form': form,
            'duplicate_detected': duplicate_detected,
        }, status=409 if form.non_field_errors() else 400)

    return render(request, 'pages/organization_create.html', {
        'create_form': OrganizationCreateForm(),
        'duplicate_detected': False,
    })


def _detail_context(request, org, *, candidate_form=None, action_error=None):
    branches = [p for p in Place.objects.filter(organization=org, deleted_at__isnull=True).order_by('pk')
        if business_team.has_action(user=request.user, target=p, action='place.view')]
    owned_places = [p for p in Place.objects.filter(owner=request.user, organization__isnull=True,
        deleted_at__isnull=True).order_by('pk')]
    for place in branches:
        current = organization_ownership.affiliation_current(place,org)
        place.affiliation_is_current=current
        place.contact_inherited = bool(current and org.phone and not (place.phone1 or place.phone2 or place.phone3))
        place.website_inherited = bool(current and org.website and not place.website)
        place.whatsapp_inherited = bool(current and org.whatsapp)
    visible_ids = organization_ownership.join_visible_places(actor=request.user, organization_id=org.pk).values('pk')
    pending = list(OrganizationPlaceRequest.objects.filter(organization=org, status='pending', place_id__in=visible_ids)
        .select_related('place').order_by('-pk'))
    pending = [r for r in pending if request.user.pk in (r.place.owner_id, org.owner_id)]
    recovery_requests = list(OrganizationPlaceRequest.objects.filter(organization=org, status='pending', relationship_kind='business').filter(Q(place__owner=request.user) | Q(organization__owner=request.user)).select_related('place', 'organization').order_by('-pk'))
    recovery_requests += [r for r in pending if r.relationship_kind != 'business']
    organization_ownership.join_recovery_rows(actor=request.user, items=recovery_requests)
    grants = list(org.team_grants.select_related('member').order_by('pk')) if org.owner_id == request.user.pk else []
    invitations = list(org.team_invitations.filter(status='PENDING').order_by('-pk')) if org.owner_id == request.user.pk else []
    action_labels={'place.view':_('Просмотр филиалов'),'place.edit':_('Редактирование филиалов'),
        'place.stats.view':_('Статистика филиалов'),'organization.view':_('Просмотр организации'),
        'organization.edit':_('Редактирование организации'),'program.manage':_('Управление общими программами'),
        'branch.create':_('Создание филиалов')}
    for grant in grants:
        grant.action_labels=[action_labels.get(action,_('Специальное разрешение')) for action in (grant.actions or [])]
    revision = getattr(org, 'content_revision', None)
    draft = ServerDraft.objects.filter(actor=request.user, target_type='organization', target_id=org.pk).order_by('-saved_at').first()
    data = {k: getattr(org, k) for k in ('name_az','name_ru','name_en','description_az','phone','whatsapp','website')}
    if revision and revision.status in ('draft','pending','rejected'):
        data.update({k:v for k,v in revision.payload.items() if k in data})
    show_current_data = request.method == 'GET' and request.GET.get('current') == '1'
    if draft and draft.source_version == org.content_version and not show_current_data:
        data.update({k:v for k,v in draft.fields.items() if k in data})
    has_details = bool(data.get('description_az') or data.get('phone') or data.get('whatsapp') or data.get('website'))
    has_branches = len(branches) > 0
    has_team = len(grants) > 0 or len(invitations) > 0
    return {
        'workspace_mode':'detail', 'organization':org, 'schema_version':publication.SCHEMA_VERSION, 'branches':branches,
        'show_current_data':show_current_data,
        'programs':list((Program.objects.filter(organization=org, archived_at__isnull=True) if org.owner_id == request.user.pk or business_team.has_action(user=request.user,target=org,action='program.manage') else Program.objects.filter(organization=org, archived_at__isnull=True, activities__place__in=branches)).distinct().order_by('pk')),
        'pending_requests':pending, 'join_recovery_requests':recovery_requests, 'owned_places':owned_places,
        'team_grants':grants, 'team_invitations':invitations,
        'can_manage_programs':business_team.has_action(user=request.user,target=org,action='program.manage'),
        'can_edit':business_team.has_action(user=request.user,target=org,action='organization.edit'),
        'can_create_branch':business_team.has_action(user=request.user,target=org,action='branch.create'),
        'is_owner':org.owner_id==request.user.pk,
        'revision':revision, 'server_draft':draft,
        'has_details':has_details, 'has_branches':has_branches, 'has_team':has_team,
        'branch_form':BranchCreateForm(auto_id='id_branch_%s'),
        'candidate_form':candidate_form or OrganizationCandidateForm(initial={**data,
            'expected_version':org.content_version,'revision_version':revision.version if revision else 0}),
        'action_error':action_error,
    }


def organization_detail(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id)
    context = _detail_context(request, org)
    receipt = request.session.get('organization_create_confirmation')
    if (request.method == 'GET' and receipt
            and receipt['token'] == request.GET.get('created')
            and receipt['organization_id'] == org.pk and receipt['actor_id'] == request.user.pk):
        context['organization_create_confirmation'] = receipt['fields']
        del request.session['organization_create_confirmation']
    return render(request, 'pages/organization_workspace.html', context)


def organization_branch(request, org_id, place_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id)
    place = Place.objects.filter(pk=place_id, organization=org, deleted_at__isnull=True).first()
    if place is None or not business_team.has_action(user=request.user,target=place,action='place.view'): raise Http404
    return render(request,'pages/organization_branch.html',{
        'organization':org,'place':place,
        'can_edit_place':business_team.has_action(user=request.user,target=place,action='place.edit'),
        'contact_source_organization':organization_ownership.affiliation_current(place,org) and bool(org.phone) and not (place.phone1 or place.phone2 or place.phone3),
    })


@require_POST
def organization_save(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id, 'organization.edit')
    form = OrganizationCandidateForm(request.POST)
    if form.is_valid():
        patch = {k:form.cleaned_data[k] or '' for k in ('name_az','name_ru','name_en','description_az','phone','whatsapp','website')}
        try:
            publication.propose(actor=request.user,target_type='organization',target_id=org.pk,
                patch=patch,schema_version=publication.SCHEMA_VERSION,
                expected_version=form.cleaned_data['expected_version'],revision_version=form.cleaned_data['revision_version'],
                submit=form.cleaned_data['submit'])
            return redirect('organization_workspace_detail',org_id=org.pk)
        except (ValidationError, PermissionDenied) as exc: _organization_save_errors(form, exc)
    return render(request,'pages/organization_workspace.html',_detail_context(request,org,candidate_form=form),status=409 if form.non_field_errors() else 400)


def _action_error(request, org, exc):
    return render(request,'pages/organization_workspace.html',_detail_context(request,org,action_error=exc),status=409)


@require_POST
def organization_join(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = Organization.objects.filter(pk=org_id,archived_at__isnull=True).first()
    if org is None: raise Http404
    try:
        place_id = int(request.POST['place_id'])
        organization_ownership.request_join(actor=request.user,place_id=place_id,organization_id=org.pk)
    except (ValueError,KeyError,ValidationError,PermissionDenied) as exc:
        if business_team.has_action(user=request.user,target=org,action='organization.view'):
            return _action_error(request,org,exc)
        return render(request,'pages/organization_connection_error.html',{},status=409)
    if business_team.has_action(user=request.user,target=org,action='organization.view'):
        return redirect('organization_workspace_detail',org_id=org.pk)
    return redirect('owner_places_dashboard')


@require_POST
def organization_confirm(request, org_id, request_id):
    if not request.user.is_authenticated: return _login(request)
    org = Organization.objects.filter(pk=org_id,archived_at__isnull=True).first()
    if org is None: raise Http404
    item = OrganizationPlaceRequest.objects.filter(pk=request_id,organization=org).first()
    if item is None or request.user.pk not in (item.place.owner_id,org.owner_id): raise Http404
    try: organization_ownership.confirm_join(actor=request.user,request_id=item.pk)
    except (ValidationError,PermissionDenied) as exc:
        if business_team.has_action(user=request.user,target=org,action='organization.view'):
            return _action_error(request,org,exc)
        return render(request,'pages/organization_connection_error.html',{},status=409)
    if business_team.has_action(user=request.user,target=org,action='organization.view'):
        return redirect('organization_workspace_detail',org_id=org.pk)
    return redirect('owner_places_dashboard')


@require_POST
def organization_detach(request, org_id, place_id):
    if not request.user.is_authenticated: return _login(request)
    org = Organization.objects.filter(pk=org_id).first()
    place = Place.objects.filter(pk=place_id,organization=org,deleted_at__isnull=True).first() if org else None
    if place is None or request.user.pk not in (place.owner_id, org.owner_id): raise Http404
    try:
        version=int(request.POST['expected_ownership_version'])
        connections.detach_access(actor=request.user,place_id=place_id,organization_id=org.pk,expected_ownership_version=version)
    except (ValueError,KeyError,ValidationError,PermissionDenied) as exc:
        if business_team.has_action(user=request.user,target=org,action='organization.view'):
            return _action_error(request,org,exc)
        return render(request,'pages/organization_connection_error.html',{},status=409)
    return redirect('organization_detach_preview',org_id=org.pk,place_id=place_id)


@require_POST
def organization_branch_create(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id, 'branch.create')
    form = BranchCreateForm(request.POST, auto_id='id_branch_%s')
    duplicate_detected=False
    if form.is_valid():
        try:
            place = business_team.create_branch(actor=request.user, organization_id=org.pk,
                values={'name_az':form.cleaned_data['name_az'], 'category_id':form.cleaned_data['category_id'].pk},
                allow_separate=form.cleaned_data['allow_separate'])
            return redirect('organization_workspace_branch', org_id=org.pk, place_id=place.pk) if business_team.has_action(user=request.user,target=place,action='place.view') else redirect('organization_workspace_detail',org_id=org.pk)
        except PermissionDenied: raise Http404
        except ValidationError as exc:
            duplicate_detected=getattr(exc,'code',None)=='possible_duplicate'
            form.add_error(None, exc)
    context = _detail_context(request,org,action_error=form.errors)
    context['branch_form'] = form
    context['branch_duplicate_detected']=duplicate_detected
    if duplicate_detected:
        context['branch_duplicates']=connections.visible_places(request.user).filter(name_az__iexact=form.cleaned_data['name_az'].strip())
    return render(request,'pages/organization_workspace.html',context,status=409 if form.non_field_errors() else 400)


def _recovery_context(request, org_id, request_id, error=False):
    item = OrganizationPlaceRequest.objects.select_related('place', 'organization').filter(pk=request_id, organization_id=org_id).first()
    if item is None or item.relationship_kind != 'business' or request.user.pk not in (item.place.owner_id, item.organization.owner_id):
        raise Http404
    organization_ownership.join_recovery_rows(actor=request.user, items=[item])
    token = organization_ownership.join_recovery_state(actor=request.user, request_id=item.pk)
    new_url = None
    if item.status == 'canceled' and item.place.deleted_at is None and item.organization.archived_at is None:
        if item.organization.owner_id == request.user.pk and organization_ownership.join_visible_places(actor=request.user).filter(pk=item.place_id).exists():
            new_url = reverse('organization_connections', args=[org_id])
        elif item.place.owner_id == request.user.pk:
            new_url = reverse('organization_connections', args=[org_id]) + '?place_ids=' + str(item.place_id)
    return {'item': item, 'expected_state': token, 'new_request_url': new_url, 'recovery_error': error}


def organization_join_recovery(request, org_id, request_id):
    if not request.user.is_authenticated:
        return _login(request)
    if request.method != 'GET':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET'])
    return render(request, 'pages/organization_join_recovery.html', _recovery_context(request, org_id, request_id))


@require_POST
def organization_cancel(request, org_id, request_id):
    if not request.user.is_authenticated:
        return _login(request)
    context = _recovery_context(request, org_id, request_id)
    if set(request.POST) - {'csrfmiddlewaretoken', 'expected_state'}:
        return render(request, 'pages/organization_join_recovery.html', {**context, 'recovery_error': True}, status=400)
    try:
        organization_ownership.cancel_join(actor=request.user, request_id=request_id, expected_state=request.POST.get('expected_state'))
    except PermissionDenied:
        raise Http404
    except ValidationError as exc:
        return render(request, 'pages/organization_join_recovery.html', _recovery_context(request, org_id, request_id, error=True), status=409 if exc.code == 'request_conflict' else 400)
    return redirect('organization_join_recovery', org_id=org_id, request_id=request_id)
