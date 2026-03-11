from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import TemplateView

from .controllers.account_controller import AccountController
from .controllers.auth_controller import AuthController
from .controllers.engagement_controller import EngagementController
from .controllers.home_controller import HomeController
from .controllers.owner_places_controller import OwnerPlacesController
from .controllers.owner_reviews_controller import OwnerReviewsController
from .controllers.owner_team_controller import OwnerTeamController
from .controllers.ownership_controller import OwnershipController
from .controllers.place_controller import PlaceController
from .controllers.seo_controller import SeoController
from .controllers.tracking_controller import TrackingController
from .models import UserProfile

home_controller = HomeController.build_default()
place_controller = PlaceController.build_default()
engagement_controller = EngagementController.build_default()
auth_controller = AuthController.build_default()
ownership_controller = OwnershipController.build_default()
owner_places_controller = OwnerPlacesController.build_default()
owner_team_controller = OwnerTeamController.build_default()
owner_reviews_controller = OwnerReviewsController.build_default()
seo_controller = SeoController.build_default()
tracking_controller = TrackingController.build_default()
account_controller = AccountController.build_default()


def _resolve_safe_next_url(request, fallback_url: str) -> str:
    target = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return fallback_url


def _redirect_to_login(request):
    query = urlencode({"next": request.get_full_path()})
    return redirect(f"{reverse('account_login')}?{query}")


def home(request):
    context = home_controller.build_context(
        request=request,
        google_maps_api_key=settings.GOOGLE_MAPS_API_KEY,
    )

    return render(
        request,
        "pages/home.html",
        context,
    )


def place_list(request):
    return _render_place_list(request)


def place_new(request):
    return _render_place_list(request, force_new_only=True)


def _render_place_list(request, force_new_only=False, created_after=None):
    context = place_controller.build_list_context(
        request,
        force_new_only=force_new_only,
        created_after=created_after,
    )

    return render(request, "catalog/place_list.html", context)


def place_detail_legacy(request, pk):
    place = place_controller.get_active_place_for_legacy_redirect(pk=pk)
    return redirect(place.get_absolute_url(), permanent=True)


def place_detail(request, pk, slug):
    place = place_controller.get_active_place_with_gallery(pk=pk)
    if slug != place.slug:
        return redirect(place.get_absolute_url(), permanent=True)

    context = place_controller.build_detail_context(request, place=place)
    context.update(ownership_controller.build_place_claim_context(request=request, place=place))

    return render(
        request,
        "catalog/place_detail.html",
        context,
    )


@require_POST
def toggle_place_like(request, pk):
    result = engagement_controller.toggle_place_like(request=request, place_id=pk)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "liked": result.liked, "likes_count": result.likes_count})

    return redirect(request.POST.get("next") or result.place.get_absolute_url())


@require_POST
def add_place_review(request, pk):
    place, result = engagement_controller.add_place_review(
        request=request,
        place_id=pk,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", True),
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{place.get_absolute_url()}#reviews")


@require_POST
def add_site_review(request):
    result = engagement_controller.add_site_review(
        request=request,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", True),
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{reverse('home')}#site-reviews")


@csrf_exempt
@require_POST
def track_event(request):
    result = tracking_controller.track_cta_event_from_json(request=request, raw_body=request.body)
    return JsonResponse(result.as_payload(), status=result.status_code)


def seo_landing(request, seo_slug):
    context = seo_controller.build_landing_context(request=request, seo_slug=seo_slug)
    return render(request, "catalog/seo_landing.html", context)


def about(request):
    return render(
        request,
        "pages/about.html",
        {"meta_description": _("О проекте KidsMap: каталог детских кружков и секций в Баку.")},
    )


def contacts(request):
    return render(
        request,
        "pages/contacts.html",
        {"meta_description": _("Контакты проекта KidsMap.")},
    )


def owner_cabinet(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context = ownership_controller.build_owner_cabinet_context(request=request)
    context.update(owner_team_controller.build_user_pending_invitations_context(request=request))
    context.update({"meta_description": _("Кабинет владельца KidsMap: заявки и управление карточками.")})
    return render(request, "pages/owner_cabinet.html", context)


def owner_places_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_places_controller.build_dashboard_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("owner_cabinet")

    context.update(
        {
            "meta_description": _("Управление карточками владельца: редактирование, черновики, публикация и статистика."),
        }
    )
    return render(request, "pages/owner_places.html", context)


def owner_place_edit(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        result = owner_places_controller.save_edit_form(
            request=request,
            place_id=pk,
            data=request.POST,
            files=request.FILES,
        )
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        context = {
            "form": result.form,
            "place": result.place,
            "owner_profile": result.profile,
            "recent_place_audits": result.place.change_audits.select_related("changed_by")[:20] if result.place else [],
            "meta_description": _("Редактирование карточки кружка в кабинете владельца."),
        }
        return render(request, "pages/owner_place_edit.html", context)

    result = owner_places_controller.build_edit_form_context(request=request, place_id=pk)
    if not result.ok or result.form is None:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context = {
        "form": result.form,
        "place": result.place,
        "owner_profile": result.profile,
        "recent_place_audits": result.place.change_audits.select_related("changed_by")[:20] if result.place else [],
        "meta_description": _("Редактирование карточки кружка в кабинете владельца."),
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


def owner_team_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_team_controller.build_manager_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("owner_cabinet")

    context.update(
        {
            "meta_description": _("Команда владельца KidsMap: приглашения, роли и управление доступами."),
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
        return redirect("owner_cabinet")
    context.update(
        {
            "meta_description": _("Команда владельца KidsMap: приглашения, роли и управление доступами."),
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
    return redirect("owner_cabinet")


@require_POST
def owner_team_reject_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.reject_invitation_for_user(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_cabinet")


def owner_reviews_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, result = owner_reviews_controller.build_context(request=request)
    if not result.ok:
        messages.error(request, result.message)
        return redirect("owner_cabinet")

    context.update(
        {
            "meta_description": _("Модерация отзывов владельца: управление публикацией отзывов по вашим кружкам."),
        }
    )
    return render(request, "pages/owner_reviews.html", context)


@require_POST
def owner_review_approve(request, review_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_reviews_controller.set_review_approval(
        request=request,
        review_id=review_id,
        is_approved=True,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_reviews_dashboard")


@require_POST
def owner_review_reject(request, review_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_reviews_controller.set_review_approval(
        request=request,
        review_id=review_id,
        is_approved=False,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_reviews_dashboard")


@require_POST
def request_place_ownership(request, pk):
    place, result = ownership_controller.submit_claim_request(request=request, place_id=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{place.get_absolute_url()}#owner-request")


def account_verify_email(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    initial_email = (request.GET.get("email") or "").strip().lower()
    initial_next = _resolve_safe_next_url(request, reverse("account_profile"))
    verify_form = auth_controller.build_email_verification_form(initial={"email": initial_email})
    resend_form = auth_controller.build_email_verification_resend_form(initial={"email": initial_email})

    if request.method == "POST":
        action = (request.POST.get("form_action") or "verify").strip().lower()
        if action == "resend":
            resend_form = auth_controller.build_email_verification_resend_form(data=request.POST)
            verify_form = auth_controller.build_email_verification_form(initial={"email": resend_form.data.get("email", "")})
            if resend_form.is_valid():
                result = auth_controller.resend_registration_verification_code(email=resend_form.cleaned_data["email"])
                if result.ok:
                    messages.success(request, result.message)
                else:
                    messages.error(request, result.message)
                query = urlencode({"email": resend_form.cleaned_data["email"], "next": initial_next})
                return redirect(f"{reverse('account_verify_email')}?{query}")
            messages.error(request, _("Проверьте email и повторите отправку кода."))
        else:
            verify_form = auth_controller.build_email_verification_form(data=request.POST)
            resend_form = auth_controller.build_email_verification_resend_form(
                initial={"email": verify_form.data.get("email", "")}
            )
            if verify_form.is_valid():
                result = auth_controller.verify_registration_email_code(
                    email=verify_form.cleaned_data["email"],
                    code=verify_form.cleaned_data["code"],
                )
                if result.ok and result.user is not None:
                    auth_login(request, result.user)
                    messages.success(request, result.message)
                    return redirect(_resolve_safe_next_url(request, reverse("account_profile")))
                messages.error(request, result.message)
            else:
                messages.error(request, _("Проверьте email и код подтверждения."))

    return render(
        request,
        "auth/verify_email.html",
        {
            "verify_form": verify_form,
            "resend_form": resend_form,
            "meta_description": _("Подтверждение email в KidsMap."),
            "next_url": initial_next,
        },
    )


class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account_dashboard.html"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        context.update(dashboard_context)
        context.update(
            {
                "is_owner_role": dashboard_context["profile_model"].role == UserProfile.ROLE_OWNER,
                "meta_description": _("Личный кабинет KidsMap: профиль, избранные кружки и история просмотров."),
            }
        )
        return context


class AccountFavoritesView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account_favorites.html"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = account_controller.ensure_profile(user=self.request.user)
        context.update(account_controller.build_favorites_context(user=self.request.user))
        context.update(
            {
                "profile_model": profile,
                "is_owner_role": profile.role == UserProfile.ROLE_OWNER,
                "meta_description": _("Избранные кружки пользователя в KidsMap."),
            }
        )
        return context


class AccountProfileView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"
    template_name = "pages/account_profile.html"

    def _build_context(self, *, profile, profile_form, password_form):
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        return {
            "profile_model": profile,
            "profile_form": profile_form,
            "password_form": password_form,
            "favorites_count": dashboard_context["favorites_count"],
            "history_count": dashboard_context["history_count"],
            "is_owner_role": profile.role == UserProfile.ROLE_OWNER,
            "meta_description": _("Личный кабинет KidsMap: данные профиля, контакты и безопасность аккаунта."),
        }

    def get(self, request, *args, **kwargs):
        profile = auth_controller.ensure_profile(user=request.user)
        profile_form = auth_controller.build_profile_edit_form(user=request.user)
        password_form = auth_controller.build_password_change_form(user=request.user)
        return render(
            request,
            self.template_name,
            self._build_context(profile=profile, profile_form=profile_form, password_form=password_form),
        )

    def post(self, request, *args, **kwargs):
        profile = auth_controller.ensure_profile(user=request.user)
        profile_form = auth_controller.build_profile_edit_form(user=request.user)
        password_form = auth_controller.build_password_change_form(user=request.user)
        current_route = request.resolver_match.url_name if request.resolver_match else "account_profile"
        if current_route not in {"account_profile", "account_settings"}:
            current_route = "account_profile"

        form_action = (request.POST.get("form_action") or "").strip().lower()
        if form_action == "profile":
            profile_form = auth_controller.build_profile_edit_form(user=request.user, data=request.POST)
            if profile_form.is_valid():
                profile = auth_controller.update_user_profile_from_form(user=request.user, form=profile_form)
                messages.success(request, _("Профиль обновлен."))
                return redirect(current_route)
            messages.error(request, _("Проверьте данные профиля и исправьте ошибки."))
        elif form_action == "password":
            password_form = auth_controller.build_password_change_form(user=request.user, data=request.POST)
            if password_form.is_valid():
                updated_user = auth_controller.update_password_from_form(form=password_form)
                update_session_auth_hash(request, updated_user)
                messages.success(request, _("Пароль успешно изменен."))
                return redirect(current_route)
            messages.error(request, _("Не удалось изменить пароль. Проверьте введенные поля."))
        else:
            messages.error(request, _("Неизвестное действие формы."))
            return redirect(current_route)

        return render(
            request,
            self.template_name,
            self._build_context(profile=profile, profile_form=profile_form, password_form=password_form),
        )


def account_dashboard(request):
    return AccountDashboardView.as_view()(request)


def account_favorites(request):
    return AccountFavoritesView.as_view()(request)


def account_profile(request):
    return AccountProfileView.as_view()(request)


def account_settings(request):
    return AccountProfileView.as_view()(request)


def account_register(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    form = auth_controller.build_registration_form(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = auth_controller.register_user_from_form(form=form)
        verification = auth_controller.send_registration_verification_code(
            user=user,
            email=form.cleaned_data["email"],
        )
        if verification.ok:
            messages.success(
                request,
                _("Регистрация почти завершена. Введите код из письма для подтверждения email."),
            )
        else:
            messages.error(request, verification.message)
        query = urlencode(
            {
                "email": form.cleaned_data["email"],
                "next": _resolve_safe_next_url(request, reverse("account_profile")),
            }
        )
        return redirect(f"{reverse('account_verify_email')}?{query}")

    return render(
        request,
        "auth/register.html",
        {
            "form": form,
            "meta_description": _("Регистрация в KidsMap: выберите тип аккаунта и начните пользоваться каталогом."),
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
        },
    )


def account_login(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    form = auth_controller.build_login_form(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        if form.cleaned_data.get("remember_me"):
            request.session.set_expiry(int(getattr(settings, "SESSION_COOKIE_AGE", 1209600)))
        else:
            request.session.set_expiry(0)
        messages.success(request, _("Вы вошли в аккаунт."))
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    return render(
        request,
        "auth/login.html",
        {
            "form": form,
            "meta_description": _("Вход в аккаунт KidsMap."),
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
        },
    )


@require_POST
def account_logout(request):
    auth_logout(request)
    messages.info(request, _("Вы вышли из аккаунта."))
    return redirect(_resolve_safe_next_url(request, reverse("home")))
