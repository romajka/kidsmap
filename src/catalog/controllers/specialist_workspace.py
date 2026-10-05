"""Person-only workspace, explicit organization consent and dedicated reviews.

All nested IDs are bound to their route parent before domain services execute.
GET never mutates; POST relies on Django's CSRF middleware. Private documents
and person contacts never enter the organization workspace context.
"""
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.forms import OwnerSpecialistForm
from catalog.models import Organization, Specialist, SpecialistDocument
from catalog.models.specialist_domain import SpecialistClaim, SpecialistEmployment
from catalog.services import specialist_documents, specialist_domain
from catalog.services.features import require_specialists_section_enabled
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile
from catalog.specialist_forms import EmploymentProposalForm, SpecialistDocumentUploadForm


def workspace(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        require_specialists_section_enabled()
        if request.method not in ('GET', 'POST'):
            return HttpResponseNotAllowed(['GET', 'POST'])
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            request.specialist_actor = specialist_domain.require_actor(request.user)
            return view(request, *args, **kwargs)
        except (PermissionDenied, PermissionError, ObjectDoesNotExist):
            raise Http404
    return wrapped


def _person(request, pk):
    person = get_object_or_404(Specialist, pk=pk)
    specialist_domain.require_person(request.specialist_actor, person)
    return person


def _organization(request, org_id):
    return get_object_or_404(Organization, pk=org_id, owner=request.specialist_actor,
                             archived_at__isnull=True)


def _claim_reviewer(actor):
    try:
        specialist_domain._reviewer(actor)
        return True
    except PermissionDenied:
        return False


def document_version(document):
    return '%s|%s|%s|%s' % (document.status, int(document.is_published),
                        document.opted_in_at.isoformat() if document.opted_in_at else '',
                        document.specialist.updated_at.isoformat())


def _current_document(document, token):
    if not token or token != document_version(document):
        raise ValidationError(_("Запись изменилась. Обновите страницу."), code='stale_version')


def _explicit_choice(value):
    if value not in ('true', 'false'):
        raise ValidationError(_("Выберите доступ к документу."))
    return value == 'true'


def _posted_id(request, key):
    value = request.POST.get(key, '')
    # Only this input boundary catches malformed integers; unrelated domain
    # errors must remain observable. Avoid oversized IDs before SQL coercion.
    if not value.isascii() or not value.isdecimal() or len(value) > 18 or int(value) < 1:
        raise Http404
    return int(value)


def _error_context(exc):
    message = (_("Запись изменилась. Обновите страницу.") if _error_status(exc) == 409
               else _("Не удалось выполнить действие. Проверьте данные и права доступа."))
    return {'errors': [message], 'error_message': message, 'error': message}


def _error_status(exc):
    return 409 if getattr(exc, 'code', '') in ('stale_version', 'claim_conflict', 'consent_conflict', 'employment_conflict') else 400


def _context(request, *, mode, specialist=None, organization=None, **extra):
    actor = request.specialist_actor
    context = {'workspace_mode': mode, 'specialist': specialist, 'organization': organization,
               'can_review_claims': _claim_reviewer(actor),
               'can_review_documents': specialist_documents.can_review_documents(actor)}
    person_access = specialist and specialist_documents.is_person(actor, specialist)
    context['can_manage_specialist'] = bool(person_access)
    if person_access and mode in ('profile', 'invitations', 'certificates'):
        context['active_practice_locations'] = list(specialist.practice_locations.filter(is_active=True)
            .select_related('place', 'region').order_by('pk'))
        context['practice_history'] = list(specialist.practice_locations.filter(is_active=False)
            .select_related('place', 'region').order_by('pk'))
    context.update(extra)
    return context


def _employment_cards(items, actor, side):
    today = timezone.localdate()
    result = list(items.select_related('specialist', 'organization').prefetch_related('history')
                  .order_by('-start_date', '-pk'))
    action_labels = {'proposed': _("Предложение отправлено"), 'person_confirmed': _("Согласие специалиста"),
                     'organization_confirmed': _("Согласие организации"), 'cancelled': _("Участие отменено")}
    for item in result:
        for event in item.history.all():
            event.action_label = action_labels.get(event.action, _("Сведения обновлены"))
        parties_current = (item.organization.archived_at is None
            and item.person_user_id == item.specialist.verified_person_user_id
            and item.specialist.person_verified_at is not None
            and item.organization_owner_id == item.organization.owner_id
            and item.organization_ownership_version == item.organization.ownership_version)
        item.can_confirm = bool(parties_current and item.status == SpecialistEmployment.PENDING
            and not getattr(item, side + '_confirmed_at'))
        item.can_confirm_person = item.can_confirm if side == 'person' else False
        item.can_confirm_organization = item.can_confirm if side == 'organization' else False
        item.can_cancel = item.status != SpecialistEmployment.CANCELLED
        if item.status == SpecialistEmployment.CANCELLED or (item.end_date and item.end_date < today):
            item.temporal_state = 'history'
        elif item.status == SpecialistEmployment.PENDING or not parties_current:
            item.temporal_state = 'pending'
        elif item.start_date > today:
            item.temporal_state = 'future'
        else:
            item.temporal_state = 'current'
    return result


@workspace
def specialist_workspace_index(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    actor = request.specialist_actor
    claim_review = _claim_reviewer(actor)
    document_review = specialist_documents.can_review_documents(actor)
    review_ids = set()
    if claim_review:
        review_ids.update(SpecialistClaim.objects.filter(status=SpecialistClaim.PENDING)
                          .values_list('specialist_id', flat=True))
    if document_review:
        review_ids.update(SpecialistDocument.objects.filter(status=SpecialistDocument.STATUS_PENDING)
                          .values_list('specialist_id', flat=True))
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='index',
        my_specialist=Specialist.objects.filter(verified_person_user=actor, person_verified_at__isnull=False).first(),
        proposals=Specialist.objects.filter(created_by=actor, verified_person_user__isnull=True).order_by('-pk'),
        claims=SpecialistClaim.objects.filter(applicant=actor).select_related('specialist').order_by('-pk'),
        review_profiles=Specialist.objects.filter(pk__in=review_ids).only('pk', 'name').order_by('pk'),
        owned_organizations=Organization.objects.filter(owner=actor, archived_at__isnull=True).order_by('pk')))


@workspace
def specialist_workspace_profile(request, pk=None):
    person = _person(request, pk) if pk is not None else None
    status = 200
    form = OwnerSpecialistForm(request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None, instance=person,
        draft_save_only=request.method == 'POST' and request.POST.get('form_action') == 'save_draft')
    if request.method == 'POST':
        try:
            result = save_owner_specialist_profile(user=request.specialist_actor, form=form,
                draft_save_only=request.POST.get('form_action') == 'save_draft',
                expected_updated_at=request.POST.get('expected_updated_at', request.POST.get('profile_version', ''))
                    if person else None)
            if result.ok:
                return redirect('specialist_workspace_profile' if person else 'specialist_workspace_claims',
                                pk=result.specialist.pk)
            form = result.form or form
            status = 400
        except ValidationError as exc:
            form.add_error(None, exc)
            status = _error_status(exc)
    return render(request, 'pages/owner_specialist_create.html', _context(request, mode='profile',
        specialist=person, form=form, profile_version=person.updated_at.isoformat() if person else '',
        specializations=form.fields['specializations'].queryset, is_proposal=person is None), status=status)


@workspace
def specialist_workspace_claims(request, pk):
    person = get_object_or_404(Specialist, pk=pk)
    actor = request.specialist_actor
    # An integer URL is not evidence that a private person's name may be read.
    # Own proposals and existing requests remain reachable after moderation.
    if not ((person.status == Specialist.STATUS_PUBLISHED and person.is_active)
            or person.created_by_id == actor.pk
            or specialist_documents.is_person(actor, person)
            or person.person_claims.filter(applicant=actor).exists()
            or _claim_reviewer(actor)):
        raise Http404
    error = {}; status = 200
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'request':
                specialist_domain.request_claim(actor=actor, specialist_id=person.pk)
            elif request.POST.get('action') == 'withdraw':
                item = get_object_or_404(SpecialistClaim, pk=_posted_id(request, 'claim_id'),
                    specialist=person, applicant=actor)
                specialist_domain.withdraw_claim(actor=actor, claim_id=item.pk,
                    expected_version=request.POST.get('expected_version'))
            else:
                raise ValidationError(_("Неизвестное действие."))
            return redirect('specialist_workspace_claims', pk=person.pk)
        except ValidationError as exc:
            error = _error_context(exc); status = _error_status(exc)
    claims = list(SpecialistClaim.objects.filter(specialist=person, applicant=actor).order_by('-pk'))
    for item in claims:
        item.can_withdraw = item.status == SpecialistClaim.PENDING
        item.status_label = _claim_status(item.status)
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='claims',
        specialist=person, claims=claims,
        can_request_claim=not person.verified_person_user_id and not any(c.can_withdraw for c in claims),
        **error), status=status)


def _employment_action(request, item, side):
    action = request.POST.get('action')
    if action == 'confirm':
        specialist_domain.confirm_employment(actor=request.specialist_actor, employment_id=item.pk,
            side=side, expected_version=request.POST.get('expected_version'))
    elif action == 'cancel':
        specialist_domain.cancel_employment(actor=request.specialist_actor, employment_id=item.pk,
            expected_version=request.POST.get('expected_version'))
    else:
        raise ValidationError(_("Неизвестное действие."))


@workspace
def specialist_workspace_invitations(request, pk):
    person = _person(request, pk)
    error = {}; status = 200
    if request.method == 'POST':
        item = get_object_or_404(SpecialistEmployment, pk=_posted_id(request, 'employment_id'), specialist=person)
        try:
            _employment_action(request, item, 'person')
            return redirect('specialist_workspace_invitations', pk=person.pk)
        except ValidationError as exc:
            error = _error_context(exc); status = _error_status(exc)
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='invitations',
        specialist=person, employments=_employment_cards(person.employment_links.all(),
            request.specialist_actor, 'person'), **error), status=status)


@workspace
def organization_specialists(request, org_id):
    org = _organization(request, org_id)
    action = request.POST.get('action') if request.method == 'POST' else None
    form = EmploymentProposalForm(request.POST if action == 'propose' else None)
    error = {}; status = 200
    if request.method == 'POST':
        try:
            if action == 'propose':
                if not form.is_valid():
                    status = 400
                else:
                    data = form.cleaned_data
                    specialist_domain.propose_employment(actor=request.specialist_actor,
                        specialist_id=data['specialist'].pk, organization_id=org.pk,
                        role=data['role'], start_date=data['start_date'], end_date=data['end_date'])
                    return redirect('organization_specialists', org_id=org.pk)
            else:
                item = get_object_or_404(SpecialistEmployment, pk=_posted_id(request, 'employment_id'), organization=org)
                _employment_action(request, item, 'organization')
                return redirect('organization_specialists', org_id=org.pk)
        except ValidationError as exc:
            error = _error_context(exc); status = _error_status(exc)
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='organization',
        organization=org, employment_form=form, employments=_employment_cards(org.specialist_employments.all(),
            request.specialist_actor, 'organization'), **error), status=status)


def _document_cards(items, actor, person_choice=False):
    documents = list(items.select_related('specialist', 'specialist__verified_person_user').order_by('-pk'))
    for doc in documents:
        doc.version_token = document_version(doc)
        doc.can_publish_choice = person_choice and doc.document_type != SpecialistDocument.TYPE_IDENTITY
        doc.can_download = specialist_documents.can_download_document(actor, doc)
    return documents


@workspace
def specialist_workspace_certificates(request, pk):
    person = _person(request, pk)
    actor = request.specialist_actor
    action = request.POST.get('action') if request.method == 'POST' else None
    form = SpecialistDocumentUploadForm(request.POST if action == 'upload' else None,
        request.FILES if action == 'upload' else None)
    error = {}; status = 200
    if request.method == 'POST':
        try:
            if action == 'upload':
                if not form.is_valid():
                    status = 400
                else:
                    data = form.cleaned_data
                    with transaction.atomic():
                        doc = specialist_documents.upload_document(actor=actor, specialist_id=person.pk,
                            uploaded_file=data['file'], document_type=data['document_type'], name=data['name'])
                        if data['publish']:
                            specialist_documents.set_document_public_choice(actor=actor, document_id=doc.pk, publish=True)
                    return redirect('specialist_workspace_certificates', pk=person.pk)
            elif action == 'choice':
                # Lock users -> person -> document consistently with stage24 services.
                with transaction.atomic():
                    locked_actor = specialist_domain.lock_actor(actor)
                    locked_person = Specialist.objects.select_for_update().get(pk=person.pk)
                    specialist_domain.require_person(locked_actor, locked_person)
                    doc = get_object_or_404(SpecialistDocument.objects.select_for_update(),
                        pk=_posted_id(request, 'document_id'), specialist=locked_person)
                    _current_document(doc, request.POST.get('document_version'))
                    specialist_documents.set_document_public_choice(actor=locked_actor,
                        document_id=doc.pk, publish=_explicit_choice(request.POST.get('publish')))
                return redirect('specialist_workspace_certificates', pk=person.pk)
            else:
                raise ValidationError(_("Неизвестное действие."))
        except ValidationError as exc:
            error = _error_context(exc); status = _error_status(exc)
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='certificates',
        specialist=person, upload_form=form, documents=_document_cards(person.documents.all(), actor, True),
        **error), status=status)


@workspace
def specialist_workspace_review(request, pk):
    actor = request.specialist_actor
    claims_allowed = _claim_reviewer(actor)
    documents_allowed = specialist_documents.can_review_documents(actor)
    if not claims_allowed and not documents_allowed:
        raise Http404
    person = get_object_or_404(Specialist, pk=pk)
    error = {}; status = 200
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action in ('claim_reject', 'document_reject') and not request.POST.get('reason', '').strip():
                raise ValidationError(_("Укажите причину отклонения."))
            if action in ('claim_approve', 'claim_reject') and claims_allowed:
                item = get_object_or_404(SpecialistClaim, pk=_posted_id(request, 'claim_id'), specialist=person)
                specialist_domain.review_claim(actor=actor, claim_id=item.pk,
                    expected_version=request.POST.get('expected_version'), approve=action == 'claim_approve',
                    reason=request.POST.get('reason', ''))
            elif action in ('document_approve', 'document_reject') and documents_allowed:
                with transaction.atomic():
                    specialist_domain.lock_actor(actor)
                    Specialist.objects.select_for_update().get(pk=person.pk)
                    doc = get_object_or_404(SpecialistDocument.objects.select_for_update(),
                        pk=_posted_id(request, 'document_id'), specialist=person)
                    _current_document(doc, request.POST.get('document_version'))
                    specialist_documents.review_document(actor=actor, document_id=doc.pk,
                        approve=action == 'document_approve', reason=request.POST.get('reason', ''))
            else:
                raise Http404
            return redirect('specialist_workspace_review', pk=person.pk)
        except ValidationError as exc:
            error = _error_context(exc); status = _error_status(exc)
    claims = list(person.person_claims.order_by('-pk')) if claims_allowed else []
    for claim in claims:
        claim.can_review = claim.status == SpecialistClaim.PENDING
        claim.status_label = _claim_status(claim.status)
    return render(request, 'pages/specialist_workspace.html', _context(request, mode='review',
        specialist=person, claims=claims,
        documents=_document_cards(person.documents.all(), actor) if documents_allowed else [],
        **error), status=status)


def _claim_status(status):
    return {SpecialistClaim.PENDING: _("На проверке"), SpecialistClaim.APPROVED: _("Подтверждено"),
            SpecialistClaim.REJECTED: _("Отклонено"), SpecialistClaim.WITHDRAWN: _("Запрос отозван")}.get(
                status, _("На проверке"))
