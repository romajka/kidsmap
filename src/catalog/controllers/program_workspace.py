"""Owner shared Program editor. Publication and business ACL stay in domain services."""
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from catalog.models import Activity, Category, Organization, Program
from catalog.services import business_team, publication
from catalog.services.permanent_place_rules import copy as t


class ProgramForm(forms.Form):
    name_az = forms.CharField(max_length=255)
    name_ru = forms.CharField(max_length=255, required=False)
    name_en = forms.CharField(max_length=255, required=False)
    description_az = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4}))
    description_ru = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4}))
    description_en = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    revision_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    impact_confirmed = forms.BooleanField(required=False)


def _authorized(user, org_id, program_id=None):
    org = Organization.objects.filter(pk=org_id, archived_at__isnull=True).first()
    if org is None or not business_team.has_action(user=user, target=org, action='program.manage'):
        raise Http404
    program = None
    if program_id is not None:
        program = Program.objects.filter(pk=program_id, organization=org, archived_at__isnull=True).first()
        if program is None or not business_team.has_action(user=user, target=program, action='program.manage'):
            raise Http404
    return org, program


def _context(org, program, form=None):
    revision = getattr(program, 'content_revision', None)
    branches = list(Activity.objects.filter(program=program, archived_at__isnull=True, place__deleted_at__isnull=True)
        .values_list('place_id', 'place__name_az').distinct().order_by('place_id'))
    initial = {name: getattr(program, name) for name in ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en')}
    initial['category'] = program.category_id
    if revision and revision.status in ('draft', 'pending', 'rejected'):
        initial.update({key: value for key, value in revision.payload.items() if key in initial})
    initial.update(expected_version=program.content_version, revision_version=revision.version if revision else 0)
    return {'organization': org, 'program': program, 'revision': revision,
            'form': form or ProgramForm(initial=initial), 'impact_branches': branches}


def program_detail(request, org_id, program_id):
    if not request.user.is_authenticated:
        raise Http404
    org, program = _authorized(request.user, org_id, program_id)
    return render(request, 'pages/program_editor.html', _context(org, program))


@require_POST
def program_create(request, org_id):
    if not request.user.is_authenticated:
        raise Http404
    org, _ = _authorized(request.user, org_id)
    name = (request.POST.get('name_az') or '').strip()
    if not name or len(name) > 255:
        return redirect('organization_workspace_detail', org_id=org.pk)
    with transaction.atomic():
        org = Organization.objects.select_for_update().get(pk=org.pk)
        _authorized(request.user, org.pk)
        program = Program.objects.create(organization=org, created_by=request.user, name_az=name)
    return redirect('organization_program_detail', org_id=org.pk, program_id=program.pk)


@require_POST
def program_save(request, org_id, program_id):
    if not request.user.is_authenticated:
        raise Http404
    org, program = _authorized(request.user, org_id, program_id)
    form = ProgramForm(request.POST)
    branches_exist = Activity.objects.filter(program=program, archived_at__isnull=True, place__deleted_at__isnull=True).exists()
    if form.is_valid():
        if branches_exist and not form.cleaned_data['impact_confirmed']:
            form.add_error('impact_confirmed', t('Проверьте затронутые филиалы перед отправкой.', 'Göndərməzdən əvvəl təsirlənən filialları yoxlayın.', 'Review affected branches before submitting.'))
        else:
            patch = {name: form.cleaned_data[name] for name in ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en')}
            patch['category'] = form.cleaned_data['category'].pk if form.cleaned_data['category'] else None
            try:
                publication.propose(actor=request.user, target_type='program', target_id=program.pk,
                    patch=patch, schema_version=publication.SCHEMA_VERSION,
                    expected_version=form.cleaned_data['expected_version'],
                    revision_version=form.cleaned_data['revision_version'], submit=bool(request.POST.get('submit')))
                return redirect('organization_program_detail', org_id=org.pk, program_id=program.pk)
            except PermissionDenied:
                raise Http404
            except ValidationError as exc:
                form.add_error(None, exc)
    return render(request, 'pages/program_editor.html', _context(org, program, form),
        status=409 if form.non_field_errors() else 400)
