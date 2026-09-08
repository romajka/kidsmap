from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.staff_roles import can_use_volunteer_workspace
from catalog.services.volunteer_places import (
    editor_form, own_places, save_proposal, require_reviewer, review_proposal,
    restart_proposal, live_snapshot, review_form,
)
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.place_schedule import build_schedule_summary
from catalog.volunteer_forms import CONTENT_FIELDS
from catalog.services.permanent_place_rules import copy as t
from catalog.services.volunteer_dashboard import dashboard_context, workspace_places, display_card
from catalog.services.volunteer_editor import editor_context
from catalog.services.place_taxonomy_config import build_place_taxonomy_config


def render(request, template, **context):
    return TemplateResponse(request, f"admin/volunteer/{template}.html", {
        **admin.site.each_context(request), **context,
    })


@require_http_methods(["GET"])
def index(request):
    return render(request, "index", title=_("Мои места"), **dashboard_context(request.user, request.GET))


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


@require_http_methods(["GET", "POST"])
def edit(request, place_id=None):
    if not can_use_volunteer_workspace(request.user):
        raise PermissionDenied
    place = get_object_or_404(own_places(request.user), pk=place_id) if place_id else Place(created_by=request.user, status="draft", is_active=False)
    revision = VolunteerPlaceRevision.objects.filter(place=place).first() if place.pk else None
    if request.method == "POST":
        action = request.POST.get("action")
        if action not in {"draft", "submit", "restart"}:
            raise PermissionDenied
        if action == "restart":
            form = editor_form(place, revision)
            try:
                restart_proposal(user=request.user, place_id=place_id, version=int(request.POST.get("revision_version", -1)))
            except (ValueError, ValidationError) as exc:
                messages.error(request, "; ".join(exc.messages) if isinstance(exc, ValidationError) else _("Обновите страницу."))
                return redirect("admin:volunteer_edit", place_id=place_id)
            else:
                messages.success(request, _("Загружена текущая версия. Предыдущий черновик заменён."))
                return redirect("admin:volunteer_edit", place_id=place_id)
        else:
            place, revision, form = save_proposal(user=request.user, place_id=place_id, data=request.POST, files=request.FILES)
            if not form.errors:
                messages.success(request, t("Место отправлено на модерацию. Статус проверки — в разделе «Мои места».", "Məkan moderasiyaya göndərildi. Statusu «Məkanlarım» bölməsində izləyə bilərsiniz.", "Place submitted for review. Track its status in My places.") if action == "submit" else t("Черновик сохранён.", "Qaralama saxlanıldı.", "Draft saved."))
                return redirect("admin:volunteer_edit", place_id=place.pk)
    else:
        form = editor_form(place, revision)
    conflict = bool(revision and revision.status != "approved" and revision.base_snapshot != live_snapshot(place))
    return render(request, "edit", title=_("Редактировать место") if place_id else _("Добавить место"),
                  form=form, adminform={"form": form}, sections=form.sections(), place=place,
                  revision=revision, conflict=conflict, volunteer_editor=True, km_place_taxonomy_picker=build_place_taxonomy_config(form), **editor_context(form),
                  card=display_card(workspace_places(request.user).get(pk=place.pk)) if place.pk else None)


@require_http_methods(["GET"])
def review_index(request):
    require_reviewer(request.user)
    revisions = VolunteerPlaceRevision.objects.filter(status="pending").select_related("place", "author").order_by("updated_at")
    return render(request, "review_index", title=_("Изменения волонтёров"), page=Paginator(revisions, 25).get_page(request.GET.get("page")))


def display_value(name, value):
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
            error = "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(_("Обновите страницу."))
        else:
            messages.success(request, _("Изменения опубликованы.") if action == "approve" else _("Возвращено на доработку."))
            return redirect("admin:volunteer_review_index")
    current = live_snapshot(revision.place)
    rows = []
    for name, proposed in revision.payload.items():
        previous = current.get(name)
        if proposed == previous:
            continue
        label = Place._meta.get_field(name).verbose_name if name in CONTENT_FIELDS else {"pricing_plans": _("Тарифы"), "structured_schedule": _("Расписание")}.get(name, name)
        row = {"label": label, "before": display_value(name, previous), "after": display_value(name, proposed)}
        if name in {"photo", "cover_photo"}:
            storage = Place._meta.get_field(name).storage
            row.update(image=True, before=storage.url(previous) if previous else "", after=storage.url(proposed) if proposed else "")
        rows.append(row)
    form = review_form(revision)
    readiness = evaluate_form_readiness(form, form.instance) if form.is_valid() else None
    return render(request, "review", title=_("Проверка изменений"), revision=revision, rows=rows,
                  error=error, readiness=readiness, validation_errors=form.errors,
                  conflict=revision.base_snapshot != current)


_original_get_urls = admin.site.get_urls


def get_urls():
    wrap = admin.site.admin_view
    return [
        path("volunteer/", wrap(index), name="volunteer_index"),
        path("volunteer/add/", wrap(edit), name="volunteer_add"),
        path("volunteer/<int:place_id>/", wrap(detail), name="volunteer_detail"),
        path("volunteer/<int:place_id>/photo/<str:kind>/", wrap(photo), name="volunteer_photo"),
        path("volunteer/<int:place_id>/edit/", wrap(edit), name="volunteer_edit"),
        path("volunteer/review/", wrap(review_index), name="volunteer_review_index"),
        path("volunteer/review/<int:place_id>/", wrap(review), name="volunteer_review"),
    ] + _original_get_urls()


admin.site.get_urls = get_urls
