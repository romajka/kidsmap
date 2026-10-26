from catalog.services.volunteer_places import revision_base_matches
from django.contrib import admin, messages
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision
from catalog.services.staff_roles import can_use_volunteer_workspace
from catalog.services.volunteer_places import (
    editor_form, own_places, save_proposal, require_reviewer, review_proposal,
    restart_proposal, live_snapshot, review_form, can_delete_working_place,
)
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.place_schedule import build_schedule_summary
from catalog.volunteer_forms import CONTENT_FIELDS
from catalog.services.permanent_place_rules import copy as t
from catalog.services.volunteer_dashboard import dashboard_context, workspace_places, display_card
from catalog.services.volunteer_editor import editor_context
from catalog.services.place_taxonomy_config import build_place_taxonomy_config
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.moderation_sla import submission_message


def render(request, template, **context):
    return TemplateResponse(request, f"admin/volunteer/{template}.html", {
        **admin.site.each_context(request), **context,
    })


@require_http_methods(["GET"])
def index(request):
    from catalog.services.volunteer_proposals import own_proposal_rows
    from catalog.services.place_editor_drafts import working_drafts_context
    context = dashboard_context(request.user, request.GET)
    drafts = working_drafts_context(user=request.user, surface='volunteer', params=request.GET)
    for card in context['cards']:
        card['working_draft'] = drafts['working_drafts_by_target'].get(card['place'].pk)
    return render(request, "index", title=_("Мои места"), proposals=own_proposal_rows(request.user), **context, **drafts)


def detail(request, place_id):
    place = get_object_or_404(workspace_places(request.user).select_related("volunteer_revision"), pk=place_id)
    if request.method != "GET":
        raise PermissionDenied
    card = display_card(place)
    return render(request, "detail", title=card["name"], card=card)


@never_cache
def photo(request, place_id, kind):
    place = get_object_or_404(own_places(request.user).select_related("volunteer_revision"), pk=place_id)
    if request.method != "GET":
        raise PermissionDenied
    if kind not in {"main", "cover"}:
        raise Http404
    revision = getattr(place, "volunteer_revision", None)
    payload = revision.payload if revision and revision.status != "approved" else {}
    fields = ("photo", "cover_photo") if kind == "main" else ("cover_photo",)
    for name in fields:
        stored = payload.get(name, str(getattr(place, name) or ""))
        if stored:
            storage = Place._meta.get_field(name).storage
            try:
                response = FileResponse(storage.open(stored, "rb"))
            except (FileNotFoundError, OSError):
                raise Http404
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "private, no-store"
            return response
    raise Http404


@require_http_methods(["POST"])
@transaction.atomic
def delete(request, place_id):
    if not can_use_volunteer_workspace(request.user):
        raise PermissionDenied
    place = get_object_or_404(
        Place.objects.select_for_update().filter(
            created_by=request.user, owner__isnull=True, deleted_at__isnull=True, is_temporary=False,
        ),
        pk=place_id,
    )
    revision = VolunteerPlaceRevision.objects.select_for_update().filter(place=place).first()
    if not can_delete_working_place(place, revision):
        raise PermissionDenied
    before = {"is_active": place.is_active, "deleted_at": place.deleted_at, "deleted_by_id": place.deleted_by_id}
    if place.soft_delete(deleted_by=request.user):
        DjangoPlaceChangeAuditRepository().create_entries(
            place=place, changed_by=request.user, source=PlaceChangeAudit.SOURCE_VOLUNTEER,
            changes={key: (before[key], getattr(place, key)) for key in before if before[key] != getattr(place, key)},
        )
    messages.success(request, t("Карточка перемещена в корзину.", "Kart səbətə köçürüldü.", "Card moved to trash."))
    return redirect("admin:volunteer_index")


@require_http_methods(["GET", "POST"])
def edit(request, place_id=None):
    from catalog.services.place_editor_drafts import config_for
    if not can_use_volunteer_workspace(request.user):
        raise PermissionDenied
    place = get_object_or_404(own_places(request.user), pk=place_id) if place_id else Place(created_by=request.user, status="draft", is_active=False)
    revision = VolunteerPlaceRevision.objects.filter(place=place).first() if place.pk else None
    if request.method == "POST":
        from django.utils import timezone
        explicit_save_cutoff = timezone.now()
        action = request.POST.get("action")
        if action not in {"draft", "submit", "restart"}:
            raise PermissionDenied
        if action == "restart":
            form = editor_form(place, revision)
            try:
                restart_proposal(user=request.user, place_id=place_id,
                    version=int(request.POST.get("revision_version", -1)), token=request.POST.get("base_token", ""))
            except (ValueError, ValidationError) as exc:
                messages.error(request, "; ".join(exc.messages) if isinstance(exc, ValidationError) else _("Обновите страницу."))
                return redirect("admin:volunteer_edit", place_id=place_id)
            else:
                messages.success(request, _("Загружена текущая версия. Предыдущие правки сохранены в истории."))
                return redirect("admin:volunteer_edit", place_id=place_id)
        else:
            place, revision, form = save_proposal(user=request.user, place_id=place_id, data=request.POST, files=request.FILES)
            if not form.errors:
                from catalog.services.server_drafts import mark_explicit_save
                if request.POST.get('server_draft_id'):
                    mark_explicit_save(user=request.user, draft_id=request.POST['server_draft_id'],
                        expected_version=request.POST.get('server_draft_version', ''), place=place,
                        target_id=place_id, cutoff=explicit_save_cutoff)
                from catalog.services.place_editor_feedback import queue_editor_result
                queue_editor_result(request, action="moderation" if action == "submit" else "draft", message=submission_message("place") if action == "submit" else t("Черновик сохранён.", "Qaralama saxlanıldı.", "Draft saved."))
                messages.success(request, submission_message('place') if action == "submit" else t("Черновик сохранён.", "Qaralama saxlanıldı.", "Draft saved."))
                return redirect("admin:volunteer_edit", place_id=place.pk)
    else:
        form = editor_form(place, revision)
    conflict = bool(revision and revision.status != "approved" and not revision_base_matches(revision, place))
    duplicate_existing_url = ""
    if getattr(form, "duplicate_existing_place_id", None):
        duplicate_existing_url = reverse("admin:volunteer_edit", args=[form.duplicate_existing_place_id])
    return render(request, "edit", title=_("Редактировать место") if place_id else _("Добавить место"),
                  form=form, adminform={"form": form}, sections=form.sections(), place=place,
                  revision=revision, conflict=conflict, volunteer_editor=True, km_place_taxonomy_picker=build_place_taxonomy_config(form), **editor_context(form),
                  km_place_draft_config=config_for(user=request.user, place=place, surface='volunteer'),
                  google_maps_api_key=settings.GOOGLE_MAPS_API_KEY,
                  card=display_card(workspace_places(request.user).get(pk=place.pk)) if place.pk else None,
                  duplicate_existing_url=duplicate_existing_url)


@require_http_methods(["GET"])
def review_index(request):
    require_reviewer(request.user)
    # This legacy screen and its decision URL are keyed by Place, while the
    # shared revision table also contains Program/Organization/Activity edits.
    revisions = VolunteerPlaceRevision.objects.filter(status="pending", place__isnull=False).select_related("place", "author").order_by("updated_at")
    return render(request, "review_index", title=_("Изменения волонтёров"), page=Paginator(revisions, 25).get_page(request.GET.get("page")))


def display_value(name, value):
    if name == 'nature':
        return {'business': t('Бизнес', 'Biznes', 'Business'),
                'public_space': t('Общественное место', 'İctimai məkan', 'Public space')}.get(value, '—')
    if name == "structured_schedule":
        return build_schedule_summary(value or []) or "—"
    if name == "pricing_plans":
        return "\n".join(" · ".join(str(plan.get(k) or "") for k in ("title_az", "title_ru", "price", "payment_type")) for plan in (value or [])) or "—"
    if name in CONTENT_FIELDS:
        field = Place._meta.get_field(name)
        if field.is_relation:
            obj = field.remote_field.model.objects.filter(**{field.target_field.name: value}).first() if value else None
            return str(obj) if obj else "—"
        if field.choices:
            return dict(field.choices).get(value, value)
    if isinstance(value, bool):
        return _("Да") if value else _("Нет")
    return str(value) if value not in (None, "") else "—"


def gallery_preview(value):
    from pathlib import PurePosixPath
    from catalog.models import PlacePhoto

    storage = PlacePhoto._meta.get_field('image').storage
    images = []
    for index, row in enumerate(value[:10] if isinstance(value, list) else []):
        if not isinstance(row, dict):
            continue
        name = row.get('image')
        if not isinstance(name, str) or not name.startswith('places/') or '\\' in name:
            continue
        path = PurePosixPath(name)
        if ('..' in path.parts or path.as_posix() != name
                or path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.heif'}):
            continue
        try:
            if not storage.exists(name):
                continue
            url = storage.url(name)
        except (OSError, ValueError):
            continue
        order = row.get('order', index)
        caption = row.get('caption', '')
        images.append({'url': url, 'caption': caption[:255] if isinstance(caption, str) else '',
                       'order': order if type(order) is int else index})
    return sorted(images, key=lambda image: image['order'])


@require_http_methods(["GET", "POST"])
def review(request, place_id):
    require_reviewer(request.user)
    revision = get_object_or_404(VolunteerPlaceRevision.objects.select_related("place", "author"), place_id=place_id)
    error = ""
    if request.method == "POST":
        action = request.POST.get("action")
        if action not in {"approve", "reject"}:
            raise PermissionDenied
        try:
            review_proposal(user=request.user, place_id=place_id, version=int(request.POST.get("version", -1)),
                            approve=action == "approve", note=request.POST.get("note", ""))
        except (ValidationError, ValueError) as exc:
            error = proposal_error(exc) if isinstance(exc, ValidationError) else str(_("Обновите страницу."))
        else:
            messages.success(request, _("Изменения опубликованы.") if action == "approve" else _("Возвращено на доработку."))
            return redirect("admin:volunteer_review_index")
    from catalog.services.publication import snapshot
    current = snapshot(revision.place, 'place')
    rows = []
    for name, proposed in revision.payload.items():
        previous = current.get(name)
        if proposed == previous:
            continue
        if name == 'gallery':
            rows.append({'label': t('Галерея', 'Qalereya', 'Gallery'), 'is_gallery': True,
                         'before_images': gallery_preview(previous), 'after_images': gallery_preview(proposed),
                         'empty_label': t('Нет фотографий', 'Şəkil yoxdur', 'No photos')})
            continue
        label = Place._meta.get_field(name).verbose_name if name in CONTENT_FIELDS else {"pricing_plans": _("Тарифы"), "structured_schedule": _("Расписание")}.get(name, name)
        if name == 'nature':
            label = t('Тип места', 'Məkanın növü', 'Place type')
        row = {"label": label, "before": display_value(name, previous), "after": display_value(name, proposed)}
        if name in {"photo", "cover_photo"}:
            storage = Place._meta.get_field(name).storage
            row.update(image=True, before=storage.url(previous) if previous else "", after=storage.url(proposed) if proposed else "")
        rows.append(row)
    form = review_form(revision)
    readiness = evaluate_form_readiness(form, form.instance) if form.is_valid() else None
    return render(request, "review", title=_("Проверка изменений"), revision=revision, rows=rows,
                  error=error, readiness=readiness, validation_errors=form.errors,
                  conflict=not revision_base_matches(revision, revision.place))


@never_cache
@require_http_methods(["GET"])
def revision_preview(request, revision_id, website=False):
    """Use the moderation ACL and the full captured candidate, never live-only data."""
    from types import SimpleNamespace
    from catalog.services import moderation_hub
    from catalog.services.admin_place_preview import build_revision_preview
    from catalog.services.admin_site_preview import render_site_preview
    row=moderation_hub.detail(request.user,'content',revision_id)
    if row['kind']!='place':raise Http404
    revision=row['revision']
    language=request.GET.get('lang',getattr(request,'LANGUAGE_CODE','ru'))
    language=language if language in ('az','ru','en') else 'ru'
    current=request.GET.get('version')=='current'
    preview=build_revision_preview(revision,language=language,current=current)
    back=reverse('admin:volunteer_moderation_detail',args=['content',revision.pk])
    inspection=reverse('admin:volunteer_revision_preview',args=[revision.pk])
    params=f'?lang={language}'+('&version=current' if current else '')
    if website:
        response=render_site_preview(request,preview,language=language,back_url=inspection+params,
            return_params={'version':'current'} if current else {})
    else:
        author=revision.author
        response=TemplateResponse(request,'admin/catalog/placeownershiprequest/preview.html',{
            **admin.site.each_context(request),'opts':Place._meta,'title':preview['title'],'preview':preview,
            'preview_is_revision':True,'preview_back_url':back,'preview_request_url':back,
            'preview_applicant_label':author.get_full_name() or author.username,
            'request_item':SimpleNamespace(pk=revision.pk,status=revision.status,get_status_display=revision.get_status_display,
                applicant=author,created_at=revision.submitted_at or revision.created_at,note='',moderation_note=revision.review_note),
            'preview_can_moderate':False,'preview_can_approve':False,
            'preview_current_url':inspection+f'?lang={language}&version=current',
            'preview_submitted_url':inspection+f'?lang={language}',
            'preview_site_url':reverse('admin:volunteer_revision_site_preview',args=[revision.pk])+params,
        })
    response['X-Robots-Tag']='noindex, nofollow, noarchive'
    response['Cache-Control']='private, no-store, max-age=0'
    return response



def proposal_error(exc):
    detail = '; '.join(exc.messages) if isinstance(exc, ValidationError) else ''
    lowered = detail.lower()
    if 'reason' in lowered or 'note' in lowered:
        return t('Укажите причину решения.', 'Qərarın səbəbini göstərin.', 'Provide a decision reason.')
    if 'name required' in lowered or 'azerbaijani name' in lowered:
        return t('Укажите название на AZ.', 'AZ dilində adı göstərin.', 'Provide an AZ name.')
    if 'already exists' in lowered or 'already current' in lowered:
        return t('Такая запись уже существует.', 'Belə qeyd artıq mövcuddur.', 'This record already exists.')
    if any(word in lowered for word in ('version', 'source conflict', 'dependency conflict', 'schema conflict', 'state conflict', 'stale')):
        return t('Данные изменились. Обновите страницу и проверьте предложение.', 'Məlumat dəyişib. Səhifəni yeniləyib təklifi yoxlayın.', 'The data changed. Reload the page and review the proposal.')
    if detail and any(ord(ch) > 127 for ch in detail):
        return detail
    return t('Проверьте введённые данные.', 'Daxil edilmiş məlumatı yoxlayın.', 'Check the submitted data.')


@require_http_methods(["GET", "POST"])
def entity_proposal(request, kind, target_id=None):
    from catalog.services import publication, volunteer_proposals, moderation_hub
    from catalog.volunteer_forms import volunteer_entity_form, VOLUNTEER_ENTITY_FIELDS
    if kind not in VOLUNTEER_ENTITY_FIELDS:
        raise Http404
    if not can_use_volunteer_workspace(request.user):
        raise PermissionDenied
    target = revision = None
    if target_id is not None:
        target, revision = volunteer_proposals.get_target(actor=request.user, kind=kind, target_id=target_id)
    initial = {**publication.snapshot(target, kind), **revision.payload} if target and revision and revision.status != 'approved' else publication.snapshot(target, kind) if target else {}
    form = volunteer_entity_form(kind, data=request.POST if request.method == 'POST' else None, initial=initial, existing=target is not None)
    error = ''
    if request.method == 'POST' and form.is_valid():
        action = request.POST.get('action')
        if action not in {'draft', 'submit'}:
            raise PermissionDenied
        patch = {name: form.cleaned_data[name] for name in VOLUNTEER_ENTITY_FIELDS[kind]}
        try:
            if target is None:
                parent_id = int(request.POST.get('parent_id') or 0) or None
                revision = volunteer_proposals.create_and_propose(actor=request.user, kind=kind, parent_id=parent_id, patch=patch, submit=action == 'submit')
            else:
                revision = volunteer_proposals.propose(actor=request.user, kind=kind, target_id=target.pk, patch=patch,
                    expected_version=int(request.POST.get('expected_version', -1)),
                    revision_version=int(request.POST.get('revision_version', -1)),
                    submit=action == 'submit', schema_version=int(request.POST.get('schema_version', -1)))
        except (ValidationError, ValueError, TypeError) as exc:
            error = proposal_error(exc)
        else:
            messages.success(request, submission_message(kind) if action == 'submit' else _('Черновик сохранён.'))
            return redirect('admin:volunteer_proposal_edit', kind=kind, target_id=getattr(revision, kind + '_id'))
    return render(request, 'entity_proposal', title=_('Предложение сведений'), kind=kind, form=form,
                  target=target, revision=revision, error=error,
                  expected_version=target.content_version if target else 0,
                  revision_version=revision.version if revision else 0,
                  schema_version=publication.SCHEMA_VERSION,
                  kind_label=moderation_hub.kind_label(kind),
                  parent_id=request.POST.get('parent_id', '') if request.method == 'POST' else request.GET.get('parent_id', ''))


@require_http_methods(["GET", "POST"])
def affiliation_proposal(request):
    from catalog.services import volunteer_proposals
    if not can_use_volunteer_workspace(request.user):
        raise PermissionDenied
    error = ''
    if request.method == 'POST':
        try:
            place_id = int(request.POST.get('place_id', 0))
            organization_id = int(request.POST.get('organization_id', 0))
            volunteer_proposals.submit_informational_link(actor=request.user, place_id=place_id, organization_id=organization_id)
        except (ValueError, TypeError, ValidationError) as exc:
            error = proposal_error(exc)
        else:
            messages.success(request, submission_message('affiliation'))
            return redirect('admin:volunteer_index')
    return render(request, 'affiliation_proposal', title=_('Предложить связь'), error=error,
                  place_id=request.POST.get('place_id', '') if request.method == 'POST' else request.GET.get('place_id', ''),
                  organization_id=request.POST.get('organization_id', '') if request.method == 'POST' else request.GET.get('organization_id', ''))


@require_http_methods(["GET"])
def moderation_hub_index(request):
    from catalog.services import moderation_hub
    entity_choices = [(kind, moderation_hub.kind_label(kind)) for kind in ('place', 'organization', 'program', 'activity', 'offering_group', 'affiliation')]
    status_choices = [(state, moderation_hub.status_label(state)) for state in ('pending', 'draft', 'rejected', 'declined', 'approved', 'canceled')]
    try:
        rows, counts = moderation_hub.query(request.user, request.GET)
    except ValidationError:
        response = render(request, 'hub_index', title=_('Центр модерации'), page=None, counts={}, filters=request.GET,
                          entity_choices=entity_choices, status_choices=status_choices,
                          error=t('Недопустимый фильтр. Проверьте значения.', 'Yanlış filtr. Dəyərləri yoxlayın.', 'Invalid filter. Check the values.'))
        response.status_code = 400
        return response
    return render(request, 'hub_index', title=_('Центр модерации'),
                  page=Paginator(rows, 25).get_page(request.GET.get('page')), counts=counts, filters=request.GET, error='',
                  entity_choices=entity_choices, status_choices=status_choices)


@require_http_methods(["GET", "POST"])
def moderation_hub_detail(request, source, item_id):
    from catalog.services import moderation_hub, volunteer_proposals
    row = moderation_hub.detail(request.user, source, item_id)
    error = ''
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            version = int(request.POST.get('version', -1))
            reason = request.POST.get('reason', '')
            if source == 'content':
                volunteer_proposals.review(actor=request.user, revision_id=item_id, version=version, action=action, reason=reason)
            else:
                volunteer_proposals.review_informational_link(actor=request.user, request_id=item_id,
                    action=action, reason=reason, expected_place_version=version)
        except (ValidationError, ValueError, TypeError) as exc:
            error = proposal_error(exc)
            row = moderation_hub.detail(request.user, source, item_id)
        else:
            messages.success(request, _('Решение сохранено.'))
            return redirect('admin:volunteer_moderation_hub')
    response = render(request, 'hub_detail', title=_('Проверка предложения'), row=row, error=error)
    if error:
        response.status_code = 409
    return response

_original_get_urls = admin.site.get_urls


def get_urls():
    wrap = admin.site.admin_view
    return [
        path("volunteer/revision/<int:revision_id>/preview/",wrap(revision_preview),name="volunteer_revision_preview"),
        path("volunteer/revision/<int:revision_id>/site-preview/",wrap(lambda request,revision_id:revision_preview(request,revision_id,website=True)),name="volunteer_revision_site_preview"),
        path("volunteer/", wrap(index), name="volunteer_index"),
        path("volunteer/add/", wrap(edit), name="volunteer_add"),
        path("volunteer/<int:place_id>/delete/", wrap(delete), name="volunteer_delete"),
        path("volunteer/<int:place_id>/photo/<str:kind>/", wrap(photo), name="volunteer_photo"),
        path("volunteer/<int:place_id>/edit/", wrap(edit), name="volunteer_edit"),
        path("volunteer/<int:place_id>/", wrap(detail), name="volunteer_detail"),
        path("volunteer/proposal/<str:kind>/add/", wrap(entity_proposal), name="volunteer_proposal_add"),
        path("volunteer/proposal/<str:kind>/<int:target_id>/", wrap(entity_proposal), name="volunteer_proposal_edit"),
        path("volunteer/affiliation/add/", wrap(affiliation_proposal), name="volunteer_affiliation_add"),
        path("volunteer/moderation/", wrap(moderation_hub_index), name="volunteer_moderation_hub"),
        path("volunteer/moderation/<str:source>/<int:item_id>/", wrap(moderation_hub_detail), name="volunteer_moderation_detail"),
        path("volunteer/review/", wrap(review_index), name="volunteer_review_index"),
        path("volunteer/review/<int:place_id>/", wrap(review), name="volunteer_review"),
    ] + _original_get_urls()


admin.site.get_urls = get_urls
