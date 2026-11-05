"""Owner workspace: places, events, team and reviews management."""

from catalog.services.place_editor_feedback import queue_editor_result
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from ..controllers import owner_events_controller
from ..controllers.owner_analytics_controller import owner_analytics_controller
from ..forms import OwnerEventForm
from ..models import Event, Place, Specialist
from ..models import FunnelEvent
from ..services.tracking import queue_google_analytics_event, track_event as track_funnel_event
from ..services.features import require_events_section_enabled
from .common import (
    _build_owner_create_draft_key,
    _redirect_to_login,
    owner_places_controller,
    owner_reviews_controller,
    owner_team_controller,
    ownership_controller,
)


def owner_places_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_places_controller.build_dashboard_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("account_profile")

    from ..services.features import is_events_section_enabled

    owner_events = []
    if is_events_section_enabled():
        from django.db.models import Q
        from catalog.services.event_domain import can_manage_event
        candidates = Event.objects.filter(deleted_at__isnull=True, organizer_resolution='resolved').filter(
            Q(organizer_organization__owner=request.user, organizer_organization__owner__is_active=True,
              organizer_organization__archived_at__isnull=True)
            | Q(organizer_specialist__verified_person_user=request.user,
                organizer_specialist__verified_person_user__is_active=True,
                organizer_specialist__person_verified_at__isnull=False, organizer_specialist__is_active=True)
        ).select_related('related_place', 'organizer_organization', 'organizer_specialist').order_by('-updated_at')
        owner_events = [event for event in candidates if can_manage_event(request.user, event)]
    owner_specialists = list(
        Specialist.objects.filter(verified_person_user=request.user, verified_person_user__is_active=True,
                                  person_verified_at__isnull=False)
        .prefetch_related("specializations").order_by("-updated_at")
    )
    from catalog.models import Organization, OrganizationPlaceRequest
    from catalog.services.business_team import has_action
    from catalog.services.organization_ownership import affiliation_current
    direct_places = list(Place.objects.filter(owner=request.user, deleted_at__isnull=True).order_by('pk'))
    context['joinable_places'] = [p for p in direct_places if p.organization_id is None]
    context['joinable_organizations'] = list(Organization.objects.filter(status='published', archived_at__isnull=True).order_by('pk')[:100])
    context['place_affiliation_requests'] = list(OrganizationPlaceRequest.objects.filter(
        place__owner=request.user, status='pending').select_related('place', 'organization').order_by('-pk'))
    from catalog.services.organization_ownership import join_recovery_rows
    join_recovery_rows(actor=request.user, items=context['place_affiliation_requests'])
    context['affiliated_places'] = [p for p in direct_places if p.organization_id and affiliation_current(p, p.organization)]
    context['informational_places'] = [p for p in context['affiliated_places'] if p.organization_relationship_kind == 'informational']
    context.update(
        {
            "owner_events": owner_events,
            "owner_specialists": owner_specialists,
            "owner_event_stats": {
                "total": len(owner_events),
                "published": sum(1 for event in owner_events if event.status == Event.STATUS_PUBLISHED),
                "active": sum(1 for event in owner_events if event.status == Event.STATUS_PUBLISHED and not event.has_ended and event.occurrence_state != 'cancelled'),
                "drafts": sum(1 for event in owner_events if event.status in {Event.STATUS_DRAFT, Event.STATUS_PENDING, Event.STATUS_REJECTED}),
                "ended": sum(1 for event in owner_events if event.occurrence_status == 'completed'),
                "cancelled": sum(1 for event in owner_events if event.occurrence_state == 'cancelled'),
            },
            "owner_specialist_stats": {
                "total": len(owner_specialists),
                "published": sum(1 for item in owner_specialists if item.status == Specialist.STATUS_PUBLISHED and item.is_active),
                "drafts": sum(1 for item in owner_specialists if item.status in {Specialist.STATUS_DRAFT, Specialist.STATUS_PENDING, Specialist.STATUS_REJECTED}),
            },
            "meta_description": _("Мои места KidsMap: редактирование, черновики, модерация и статистика."),
        }
    )
    return render(request, "pages/owner_places.html", context)

def owner_place_analytics(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)
    context = owner_analytics_controller.build_context(request=request, place_id=pk)
    return render(request, "pages/owner_analytics.html", context)

def _build_owner_taxonomy_picker_config(form):
    from ..models import Category, Subcategory
    from django.db.models import Count

    category_field = form.fields.get("category")
    subcategory_field = form.fields.get("subcategory")
    if category_field is None or subcategory_field is None:
        return {"categories": [], "subcategories": []}

    categories = []
    category_queryset = category_field.queryset.order_by("order", "name_ru", "name")
    subcategory_counts = {
        item["category_id"]: item["total"]
        for item in Subcategory.active.filter(category__in=category_queryset)
        .values("category_id")
        .annotate(total=Count("pk"))
    }
    for category in category_queryset:
        categories.append(
            {
                "code": category.pk,
                "label": str(category.name_i18n()),
                "icon": category.icon_file_url,
                "icon_class": category.icon_name if category.icon_is_font_class else "",
                "color_bg": category.resolved_color_bg,
                "color_text": category.resolved_color_text,
                "subcategory_count": int(subcategory_counts.get(category.pk, 0) or 0),
            }
        )

    subcategories = []
    for subcategory in subcategory_field.queryset.order_by("category__order", "order", "name_ru", "name"):
        subcategories.append(
            {
                "id": str(subcategory.pk),
                "category": subcategory.category_id,
                "label": str(subcategory.name_i18n()),
                "icon": subcategory.icon_file_url,
            }
        )

    return {
        "categories": categories,
        "subcategories": subcategories,
    }

def owner_place_create(request):
    explicit_save_cutoff = timezone.now()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "GET" and request.GET.get("type") != "permanent":
        result = owner_places_controller.build_create_form_context(request=request)
        if not result.ok:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")
        return render(
            request,
            "pages/owner_listing_type_select.html",
            {
                "meta_description": _("Выбор типа объявления KidsMap."),
            },
        )

    if request.method == "POST":
        draft_client_key = _build_owner_create_draft_key(request, prefix="owner-place-create")
        form_action = (request.POST.get("form_action") or "").strip()
        place_post_data = request.POST.copy()
        place_post_data["is_temporary"] = ""
        place_post_data["temporary_start"] = ""
        place_post_data["temporary_end"] = ""
        if form_action == "check_coordinates":
            result = owner_places_controller.preview_create_coordinates(
                request=request,
                data=place_post_data,
                files=request.FILES,
            )
            if result.form is None:
                messages.error(request, result.message)
                return redirect("owner_places_dashboard")
            if result.message:
                if result.ok:
                    messages.success(request, result.message)
                else:
                    messages.error(request, result.message)
            context = {
                "form": result.form,
                "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
                "meta_description": _("Создание места в личном кабинете KidsMap."),
                "draft_client_key": draft_client_key,
                "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
            }
            return render(request, "pages/owner_place_create.html", context)

        if form_action in {"save_draft", "save_draft_exit"}:
            result = owner_places_controller.create_place(
                request=request,
                data=place_post_data,
                files=request.FILES,
                draft_save_only=True,
            )
            if result.ok:
                from catalog.services.server_drafts import mark_explicit_save
                mark_explicit_save(user=request.user, draft_id=request.POST.get('server_draft_id'), expected_version=request.POST.get('server_draft_version'), place=result.place, target_id=None, cutoff=explicit_save_cutoff)
                queue_editor_result(request, action="draft", message=result.message)
                messages.success(request, result.message)
                return redirect("owner_places_dashboard")

            if result.form is None:
                messages.error(request, result.message)
                return redirect("owner_places_dashboard")

            context = {
                "form": result.form,
                "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
                "meta_description": _("Создание места в личном кабинете KidsMap."),
                "draft_client_key": draft_client_key,
                "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
            }
            return render(request, "pages/owner_place_create.html", context)

        result = owner_places_controller.create_place(
            request=request,
            data=place_post_data,
            files=request.FILES,
        )
        if result.ok:
            from catalog.services.server_drafts import mark_explicit_save
            mark_explicit_save(user=request.user, draft_id=request.POST.get('server_draft_id'), expected_version=request.POST.get('server_draft_version'), place=result.place, target_id=None, cutoff=explicit_save_cutoff)
            queue_editor_result(request, action="moderation", message=result.message)
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        context = {
            "form": result.form,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Создание места в личном кабинете KidsMap."),
            "draft_client_key": draft_client_key,
            "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
        }
        return render(request, "pages/owner_place_create.html", context)

    result = owner_places_controller.build_create_form_context(request=request)
    if not result.ok or result.form is None:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context = {
        "form": result.form,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "meta_description": _("Создание места в личном кабинете KidsMap."),
        "draft_client_key": _build_owner_create_draft_key(request, prefix="owner-place-create"),
        "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
    }
    return render(request, "pages/owner_place_create.html", context)

def owner_event_create(request):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        result = owner_events_controller.create_event(
            request=request,
            data=request.POST,
            files=request.FILES,
            draft_save_only=draft_save_only
        )
        if result.ok:
            messages.success(request, result.message)
            request.session['owner_event_explicit_save'] = {'key': f"km-owner-event-v2:{request.user.pk}:{'create'}", 'entity': str(result.event.pk), 'revision': result.event.updated_at.isoformat()}
            return redirect("owner_event_edit", pk=result.event.pk) if draft_save_only else redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        form = result.form
    else:
        related_place = (request.GET.get("related_place") or "").strip()
        form = OwnerEventForm(
            user=request.user,
            initial={"related_place": related_place} if related_place else None,
        )

    return render(
        request,
        "pages/owner_event_form.html",
        {
            **owner_events_controller.entry_context(request, form, error_code=result.error_code if request.method == 'POST' else ''),
            "form": form,
            "event": None,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Создание временного мероприятия KidsMap."),
        },
    )

def owner_event_edit(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        result = owner_events_controller.edit_event(
            request=request,
            pk=pk,
            data=request.POST,
            files=request.FILES,
            draft_save_only=draft_save_only
        )
        if result.ok:
            messages.success(request, result.message)
            request.session['owner_event_explicit_save'] = {'key': f"km-owner-event-v2:{request.user.pk}:{result.event.pk}", 'entity': str(result.event.pk), 'revision': result.event.updated_at.isoformat()}
            return redirect("owner_event_edit", pk=result.event.pk) if draft_save_only else redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        form = result.form
        event = result.event
    else:
        event = owner_events_controller._managed_event(request, pk)
        if event.status in {Event.STATUS_PENDING, Event.STATUS_PUBLISHED}:
            messages.error(request, _("Tədbir yalnız qaralama və ya rədd edildikdən sonra redaktə oluna bilər."))
            return redirect("owner_places_dashboard")

        form = OwnerEventForm(instance=event, user=request.user)

    return render(
        request,
        "pages/owner_event_form.html",
        {
            **owner_events_controller.entry_context(request, form, event, error_code=result.error_code if request.method == 'POST' else ''),
            "form": form,
            "event": event,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Редактирование временного мероприятия KidsMap."),
        },
    )

@require_POST
def owner_event_submit_review(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_events_controller.submit_event_for_review(request=request, pk=pk)
    if result.ok:
        messages.success(request, result.message)
        return redirect("owner_places_dashboard")

    messages.error(request, result.message)
    if result.event and result.event.status != Event.STATUS_PENDING:
        return redirect("owner_event_edit", pk=pk)
    return redirect("owner_places_dashboard")

@require_POST
def owner_event_repeat(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)
    result = owner_events_controller.repeat_event(request=request, pk=pk)
    if result.ok:
        messages.success(request, result.message)
        return redirect('owner_event_edit', pk=result.event.pk)
    messages.error(request, result.message)
    return redirect('owner_event_manage', pk=pk)

@require_POST
def owner_event_delete(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_events_controller.delete_event(request=request, pk=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

def _owner_event_management_response(request, event, form=None, error_code='', reschedule=False):
    from zoneinfo import ZoneInfo
    from catalog.controllers.owner_events_controller import EventOccurrenceForm
    initial = {'expected_updated_at': event.updated_at.isoformat()}
    for name in ('start_datetime', 'end_datetime'):
        value = getattr(event, name)
        initial[name] = timezone.localtime(value, ZoneInfo('Asia/Baku')) if value else None
    return render(request, 'pages/owner_event_manage.html', {'event': event, 'occurrence_form': form or EventOccurrenceForm(initial=initial),
        'event_error_code': error_code, 'reschedule_action': reschedule,
        'can_reschedule': bool(event.start_datetime and event.start_datetime > timezone.now() and event.occurrence_state != 'cancelled')})

def owner_event_manage(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)
    event = owner_events_controller._managed_event(request, pk)
    return _owner_event_management_response(request, event)

@require_POST
def owner_event_cancel(request, pk):
    return _owner_event_occurrence_action(request, pk, False)

@require_POST
def owner_event_reschedule(request, pk):
    return _owner_event_occurrence_action(request, pk, True)

def _owner_event_occurrence_action(request, pk, reschedule):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)
    result = owner_events_controller.change_occurrence(request, pk, reschedule=reschedule)
    if result.ok:
        messages.success(request, result.message)
        return redirect('owner_event_manage', pk=pk)
    return _owner_event_management_response(request, result.event, result.form, result.error_code, reschedule)

def _place_revision_context(place):
    from catalog.models import VolunteerPlaceRevision
    from catalog.services.place_readiness import inherited_contact
    return {'place_revision': VolunteerPlaceRevision.objects.filter(place=place).first(), 'inherited_contact_source': bool(inherited_contact(place))} if place else {}

def owner_place_edit(request, pk):
    explicit_save_cutoff = timezone.now()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        place_post_data = request.POST.copy()
        place_post_data["is_temporary"] = ""
        place_post_data["temporary_start"] = ""
        place_post_data["temporary_end"] = ""
        result = owner_places_controller.save_edit_form(
            request=request,
            place_id=pk,
            data=place_post_data,
            files=request.FILES,
            force_coordinate_refresh=form_action == "refresh_coordinates",
            draft_save_only=form_action in {"save_draft", "save_draft_exit"},
            submit_for_moderation=form_action == "save_and_publish",
        )
        if result.ok:
            from catalog.services.server_drafts import mark_explicit_save
            mark_explicit_save(user=request.user, draft_id=request.POST.get('server_draft_id'), expected_version=request.POST.get('server_draft_version'), place=result.place, target_id=pk, cutoff=explicit_save_cutoff)
            queue_editor_result(request, action="moderation" if form_action == "save_and_publish" else "draft" if form_action in {"save_draft", "save_draft_exit"} else "save", message=result.message)
            messages.success(request, result.message)
            if form_action == "save_draft_exit":
                return redirect("owner_places_dashboard")
            if form_action in {"refresh_coordinates", "save_draft"}:
                return redirect("owner_place_edit", pk=pk)
            return redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        context = {
            "form": result.form,
            "place": result.place,
            **_place_revision_context(result.place),
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Редактирование места в личном кабинете KidsMap."),
            "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
        }
        return render(request, "pages/owner_place_edit.html", context)

    result = owner_places_controller.build_edit_form_context(request=request, place_id=pk)
    if not result.ok or result.form is None:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context = {
        "form": result.form,
        "place": result.place,
        **_place_revision_context(result.place),
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "meta_description": _("Редактирование места в личном кабинете KidsMap."),
        "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
    }
    return render(request, "pages/owner_place_edit.html", context)

@require_POST
def owner_place_publish(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.set_publication_state(request=request, place_id=pk, is_active=True)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

@require_POST
def owner_place_draft(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.set_publication_state(request=request, place_id=pk, is_active=False)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

@require_POST
def owner_place_submit_review(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.submit_for_moderation(request=request, place_id=pk)
    if result.ok:
        queue_editor_result(request, action="moderation", message=result.message)
        messages.success(request, result.message, extra_tags="mappy-submitted")
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

@require_POST
def owner_place_delete(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.delete_place(request=request, place_id=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

@require_POST
def owner_place_gallery_photo_delete(request, pk, photo_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.delete_gallery_photo(
        request=request,
        place_id=pk,
        photo_id=photo_id,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_place_edit", pk=pk)

def owner_team_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_team_controller.build_manager_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("owner_places_dashboard")

    context.update(
        {
            "meta_description": _("Команда KidsMap: приглашения, роли и управление доступом к вашим местам."),
        }
    )
    return render(request, "pages/owner_team.html", context)

@require_POST
def owner_team_invite(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.submit_invitation(request=request)
    if result.ok:
        messages.success(request, result.message)
        return redirect("owner_team_dashboard")

    messages.error(request, result.message)
    context, access = owner_team_controller.build_manager_context(request=request, form=result.form)
    if not access.ok:
        return redirect("owner_places_dashboard")
    context.update(
        {
            "meta_description": _("Команда KidsMap: приглашения, роли и управление доступом к вашим местам."),
        }
    )
    return render(request, "pages/owner_team.html", context)

@require_POST
def owner_team_cancel_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.cancel_invitation(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")

@require_POST
def owner_team_update_member_role(request, membership_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.update_member_role(request=request, membership_id=membership_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")

@require_POST
def owner_team_remove_member(request, membership_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.remove_member(request=request, membership_id=membership_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")

@require_POST
def owner_team_accept_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.accept_invitation_for_user(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

@require_POST
def owner_team_reject_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.reject_invitation_for_user(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")

def owner_reviews_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, result = owner_reviews_controller.build_context(request=request)
    if not result.ok:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context.update(
        {
            "meta_description": _("Модерация отзывов: управление публикацией отзывов по вашим местам."),
        }
    )
    return render(request, "pages/owner_reviews.html", context)

@require_POST
def owner_review_approve(request, review_id):
    from django.http import HttpResponseForbidden
    return HttpResponseForbidden()

@require_POST
def owner_review_reject(request, review_id):
    from django.http import HttpResponseForbidden
    return HttpResponseForbidden()

@require_POST
def request_place_ownership(request, pk):
    place, result = ownership_controller.submit_claim_request(request=request, place_id=pk)
    if result.ok:
        track_funnel_event(
            request=request,
            event_type=FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
            place=place,
            meta={"source": "place_claim_form"},
        )
        queue_google_analytics_event(
            request=request,
            name=FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
            params={
                "place_id": place.id,
                "page_type": "claim_place",
            },
        )
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(place.get_absolute_url())
