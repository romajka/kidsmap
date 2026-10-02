"""Owner organization screens. Domain services remain the only mutation/ACL authority."""
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from catalog.models import Category, Organization, OrganizationPlaceRequest, Place, Program, ServerDraft
from catalog.services import business_team, organization_ownership, publication


class OrganizationCreateForm(forms.Form):
    name_az = forms.CharField(max_length=255)
    name_ru = forms.CharField(max_length=255, required=False)
    name_en = forms.CharField(max_length=255, required=False)
    description_az = forms.CharField(required=False, widget=forms.Textarea)
    phone = forms.CharField(max_length=50, required=False)
    whatsapp = forms.CharField(max_length=50, required=False)
    website = forms.URLField(required=False)
    allow_separate = forms.BooleanField(required=False)


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


@require_POST
def organization_create(request):
    if not request.user.is_authenticated: return _login(request)
    form = OrganizationCreateForm(request.POST)
    if form.is_valid():
        values = {k: v for k, v in form.cleaned_data.items() if k != 'allow_separate' and v}
        try:
            org = organization_ownership.create_organization(actor=request.user, values=values,
                allow_separate=form.cleaned_data['allow_separate'])
            return redirect('organization_workspace_detail', org_id=org.pk)
        except PermissionDenied: raise Http404
        except ValidationError as exc: form.add_error(None, exc)
    return render(request, 'pages/organization_workspace.html', {
        'organizations': _owned_and_accessible_orgs(request.user), 'standalone_places': _standalone_places(request.user), 'create_form': form,
        'workspace_mode': 'index',
    }, status=409 if form.non_field_errors() else 400)


def _detail_context(request, org, *, candidate_form=None, action_error=None):
    branches = [p for p in Place.objects.filter(organization=org, deleted_at__isnull=True).order_by('pk')
        if business_team.has_action(user=request.user, target=p, action='place.view')]
    owned_places = [p for p in Place.objects.filter(owner=request.user, organization__isnull=True,
        deleted_at__isnull=True).order_by('pk')]
    for place in branches:
        current = organization_ownership.affiliation_current(place,org)
        place.contact_inherited = bool(current and org.phone and not (place.phone1 or place.phone2 or place.phone3))
        place.website_inherited = bool(current and org.website and not place.website)
        place.whatsapp_inherited = bool(current and org.whatsapp)
    pending = list(OrganizationPlaceRequest.objects.filter(organization=org, status='pending')
        .select_related('place').order_by('-pk'))
    pending = [r for r in pending if request.user.pk in (r.place.owner_id, org.owner_id)]
    grants = list(org.team_grants.select_related('member').order_by('pk')) if org.owner_id == request.user.pk else []
    invitations = list(org.team_invitations.filter(status='PENDING').order_by('-pk')) if org.owner_id == request.user.pk else []
    revision = getattr(org, 'content_revision', None)
    draft = ServerDraft.objects.filter(actor=request.user, target_type='organization', target_id=org.pk).order_by('-saved_at').first()
    data = {k: getattr(org, k) for k in ('name_az','name_ru','name_en','description_az','phone','whatsapp','website')}
    if revision and revision.status in ('draft','pending','rejected'):
        data.update({k:v for k,v in revision.payload.items() if k in data})
    if draft and draft.source_version == org.content_version:
        data.update({k:v for k,v in draft.fields.items() if k in data})
    return {
        'workspace_mode':'detail', 'organization':org, 'schema_version':publication.SCHEMA_VERSION, 'branches':branches,
        'programs':list((Program.objects.filter(organization=org, archived_at__isnull=True) if org.owner_id == request.user.pk or business_team.has_action(user=request.user,target=org,action='program.manage') else Program.objects.filter(organization=org, archived_at__isnull=True, activities__place__in=branches)).distinct().order_by('pk')),
        'pending_requests':pending, 'owned_places':owned_places,
        'team_grants':grants, 'team_invitations':invitations,
        'can_manage_programs':business_team.has_action(user=request.user,target=org,action='program.manage'),
        'can_edit':business_team.has_action(user=request.user,target=org,action='organization.edit'),
        'can_create_branch':business_team.has_action(user=request.user,target=org,action='branch.create'),
        'is_owner':org.owner_id==request.user.pk,
        'revision':revision, 'server_draft':draft,
        'branch_form':BranchCreateForm(auto_id='id_branch_%s'),
        'candidate_form':candidate_form or OrganizationCandidateForm(initial={**data,
            'expected_version':org.content_version,'revision_version':revision.version if revision else 0}),
        'action_error':action_error,
    }


def organization_detail(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id)
    return render(request, 'pages/organization_workspace.html', _detail_context(request, org))


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
        except (ValidationError, PermissionDenied) as exc: form.add_error(None, exc)
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
        organization_ownership.detach(actor=request.user,place_id=place_id,organization_id=org.pk,expected_ownership_version=version)
    except (ValueError,KeyError,ValidationError,PermissionDenied) as exc:
        if business_team.has_action(user=request.user,target=org,action='organization.view'):
            return _action_error(request,org,exc)
        return render(request,'pages/organization_connection_error.html',{},status=409)
    if business_team.has_action(user=request.user,target=org,action='organization.view'):
        return redirect('organization_workspace_detail',org_id=org.pk)
    return redirect('owner_places_dashboard')


@require_POST
def organization_branch_create(request, org_id):
    if not request.user.is_authenticated: return _login(request)
    org = _organization(request, org_id, 'branch.create')
    form = BranchCreateForm(request.POST, auto_id='id_branch_%s')
    if form.is_valid():
        try:
            place = business_team.create_branch(actor=request.user, organization_id=org.pk,
                values={'name_az':form.cleaned_data['name_az'], 'category_id':form.cleaned_data['category_id'].pk},
                allow_separate=form.cleaned_data['allow_separate'])
            return redirect('organization_workspace_branch', org_id=org.pk, place_id=place.pk) if business_team.has_action(user=request.user,target=place,action='place.view') else redirect('organization_workspace_detail',org_id=org.pk)
        except PermissionDenied: raise Http404
        except ValidationError as exc: form.add_error(None, exc)
    context = _detail_context(request,org,action_error=form.errors)
    context['branch_form'] = form
    return render(request,'pages/organization_workspace.html',context,status=409 if form.non_field_errors() else 400)
