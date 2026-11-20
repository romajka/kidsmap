from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from catalog.services.permanent_place_rules import copy as t
from . import services, sources
from .forms import AppealForm, DecisionForm
from .models import Appeal
from .presentation import STATUS_LABELS, kind_label, present


def _key(decision):
    return decision.kind, decision.source_id, decision.version


def _form(decision, data=None):
    return AppealForm(data, auto_id=f"appeal-{decision.kind}-{decision.source_id}-{decision.version}-%s")


def _focus_first_error(form):
    for field in form.fields:
        if field in form.errors:
            form.fields[field].widget.attrs["autofocus"] = True
            break


def _inbox(request, *, invalid_decision=None, bound_form=None, status=200):
    appeals = [present(row) for row in Appeal.objects.filter(appellant=request.user).order_by("-submitted_at", "-pk")]
    submitted = {(row.kind, row.source_id, row.source_version) for row in appeals}
    available = [decision for decision in sources.rejected_decisions(request.user) if _key(decision) not in submitted]
    # Two authorized people may receive the same specialist decision. Share its
    # appeal status, never the other applicant's identity, explanation or proof.
    shared = {
        (kind, pk, version): t(*STATUS_LABELS[state])
        for kind, pk, version, state in Appeal.objects.filter(
            kind="specialist", source_id__in=[d.source_id for d in available if d.kind == "specialist"],
        ).values_list("kind", "source_id", "source_version", "status")
    }
    decisions = []
    for decision in available:
        key = _key(decision)
        decisions.append({
            "decision": decision, "kind_label": kind_label(decision.kind), "shared_status_label": shared.get(key),
            "form": bound_form if key == invalid_decision else _form(decision),
            "submit_url": reverse("appeal_submit", args=key),
        })
    return render(request, "moderation_appeals/inbox.html", {"decisions": decisions, "appeals": appeals}, status=status)


@never_cache
@login_required(login_url="account_login")
@require_GET
def inbox(request):
    return _inbox(request)


@never_cache
@login_required(login_url="account_login")
@require_POST
def submit(request, kind, source_id, version):
    decision = sources.rejected_decision(request.user, kind, source_id, version)
    if decision is None:
        raise Http404
    form = _form(decision, request.POST)
    if not form.is_valid():
        _focus_first_error(form)
        return _inbox(request, invalid_decision=_key(decision), bound_form=form, status=400)
    try:
        appeal = services.submit_appeal(request.user, decision, **form.cleaned_data)
    except services.AppealError as exc:
        if exc.code == "already_appealed":
            return redirect("appeal_inbox")
        if exc.code in {"stale", "forbidden"}:
            raise Http404 from exc
        form.add_error(None, t("Проверьте данные заявки.", "Müraciətin məlumatlarını yoxlayın.", "Check the appeal details."))
        return _inbox(request, invalid_decision=_key(decision), bound_form=form, status=409)
    messages.success(request, t("Апелляция подана.", "Apellyasiya göndərildi.", "Appeal submitted."))
    return redirect(reverse("appeal_inbox", fragment=f"appeal-{appeal.pk}"))


@require_GET
def queue(request):
    if not services.can_access_queue(request.user):
        raise PermissionDenied
    status = request.GET.get("status", "open")
    if status not in STATUS_LABELS:
        return HttpResponseBadRequest()
    rows = services.review_queue(request.user).select_related("reviewer")
    if status == "open":
        rows = rows.filter(status__in=("submitted", "second_review"))
    elif status != "all":
        rows = rows.filter(status=status)
    page = Paginator(rows.order_by("submitted_at", "pk"), 40).get_page(request.GET.get("page"))
    page.object_list = [present(row) for row in page.object_list]
    return render(request, "moderation_appeals/queue.html", {
        **admin.site.each_context(request), "title": t("Апелляции", "Apellyasiyalar", "Appeals"),
        "appeals": page, "status": status, "filters": [(key, t(*labels)) for key, labels in STATUS_LABELS.items()],
    })


@require_http_methods(["GET", "POST"])
def review(request, pk):
    if not services.can_access_queue(request.user):
        raise PermissionDenied
    scoped = services.review_queue(request.user).select_related("reviewer", "original_reviewer", "appellant")
    appeal = get_object_or_404(scoped, pk=pk)
    form = DecisionForm()
    status = 200
    appeal_error = ""
    if request.method == "POST":
        action = request.POST.get("action")
        if action not in {"claim", "approve", "reject"}:
            return HttpResponseBadRequest()
        try:
            if action == "claim":
                services.claim_appeal(request.user, pk)
            else:
                if not services.can_decide(request.user, appeal):
                    raise PermissionDenied
                form = DecisionForm(request.POST)
                if form.is_valid():
                    services.resolve_appeal(request.user, pk, approved=(action == "approve"), reason=form.cleaned_data["reason"])
                else:
                    _focus_first_error(form)
                    status = 400
        except services.AppealError as exc:
            if exc.code == "forbidden":
                raise PermissionDenied from exc
            appeal = get_object_or_404(scoped, pk=pk)
            appeal_error = t("Состояние апелляции изменилось. Проверьте её статус.",
                             "Apellyasiyanın vəziyyəti dəyişib. Statusunu yoxlayın.",
                             "The appeal has changed. Check its status.")
            status = 409
        if status == 200:
            return redirect("appeal_review", pk=pk)
    return render(request, "moderation_appeals/review.html", {
        **admin.site.each_context(request), "title": t("Рассмотрение апелляции", "Apellyasiyaya baxış", "Appeal review"),
        "appeal": present(appeal), "form": form, "can_claim": services.can_claim(request.user, appeal),
        "can_decide": services.can_decide(request.user, appeal),
        "source_url": sources.admin_source_url(appeal.kind, appeal.source_id), "appeal_error": appeal_error,
    }, status=status)
