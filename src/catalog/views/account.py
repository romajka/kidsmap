"""Account pages: registration, login, profile, email verification, deletion."""

from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.contrib.auth import views as auth_views
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import TemplateView
from ..services.email_change import EmailChangeError, copy as email_change_copy, pending_for as pending_email_change_for
from ..forms import UserPasswordResetForm
from ..models import AccountDeletionRequest
from ..models import FunnelEvent
from ..services.account_deletion import (
    AccountDeletionError,
    cancel_account_deletion,
    confirmation_code_ttl_minutes,
    confirm_account_deletion,
    get_active_retention_policy,
    issue_cancellation_code,
    make_status_token,
    policy_from_request,
    request_account_deletion,
    typed_confirmation_phrase,
    verify_status_token,
)
from ..services.tracking import queue_google_analytics_event, track_event as track_funnel_event
from .common import (
    AUTH_INTENT_ADD_PLACE,
    _build_managed_places_summary,
    _resolve_auth_intent,
    _resolve_safe_next_url,
    account_controller,
    auth_controller,
)


def account_verify_email(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    initial_email = (request.GET.get("email") or "").strip().lower()
    initial_next = _resolve_safe_next_url(request, reverse("account_profile"))
    auth_intent = _resolve_auth_intent(request)
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
                query = urlencode({"email": resend_form.cleaned_data["email"], "next": initial_next, "intent": auth_intent})
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
                    if auth_intent == AUTH_INTENT_ADD_PLACE:
                        track_funnel_event(
                            request=request,
                            event_type=FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
                            meta={"intent": auth_intent},
                        )
                        queue_google_analytics_event(
                            request=request,
                            name=FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
                            params={
                                "page_type": "add_place_signup",
                                "intent": auth_intent,
                            },
                        )
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
            "auth_intent": auth_intent,
        },
    )

class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account_dashboard.html"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        from catalog.services.place_working_drafts import working_drafts_overview
        context = super().get_context_data(**kwargs)
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        context.update(dashboard_context)
        context.update(_build_managed_places_summary(self.request.user))
        context.update(working_drafts_overview(user=self.request.user))
        context.update(
            {
                "meta_description": _("Личный кабинет KidsMap: профиль, избранное, история просмотров и мои места."),
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
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        context.update(dashboard_context)
        context.update(_build_managed_places_summary(self.request.user))
        context.update(
            {
                "profile_model": profile,
                "meta_description": _("Избранные кружки пользователя в KidsMap."),
            }
        )
        return context

class AccountProfileView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"
    template_name = "pages/account_profile.html"

    def _build_context(self, *, profile, profile_form, password_form):
        from catalog.services.place_working_drafts import working_drafts_overview
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        current_route = self.request.resolver_match.url_name if self.request.resolver_match else "account_profile"
        managed_places_summary = _build_managed_places_summary(self.request.user)
        try:
            deletion_policy = get_active_retention_policy()
        except AccountDeletionError:
            deletion_policy = None
        active_deletion = AccountDeletionRequest.objects.filter(
            user=self.request.user,
            status__in=AccountDeletionRequest.ACTIVE_STATUSES,
        ).first()
        is_staff_user = bool(self.request.user.is_staff or self.request.user.is_superuser)
        pending_staff_deletion = None
        if is_staff_user:
            pending_staff_deletion = AccountDeletionRequest.objects.filter(
                user=self.request.user,
                status=AccountDeletionRequest.Status.HELD,
                hold_code="STAFF_OFFBOARDING_REVIEW",
            ).first()

        return {
            "profile_model": profile,
            "profile_form": profile_form,
            "pending_email_change": pending_email_change_for(self.request.user),
            "password_form": password_form,
            "favorites_count": dashboard_context["favorites_count"],
            "history_count": dashboard_context["history_count"],
            **managed_places_summary,
            **(working_drafts_overview(user=self.request.user) if current_route != 'account_settings' else {}),
            "is_settings_view": current_route == "account_settings",
            "account_deletion_available": deletion_policy is not None and not is_staff_user,
            "account_deletion_staff_blocked": is_staff_user,
            "active_account_deletion": active_deletion,
            "pending_staff_deletion": pending_staff_deletion,
            "staff_deletion_form": auth_controller.build_staff_account_deletion_review_form(),
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
            profile_form = auth_controller.build_profile_edit_form(user=request.user, data=request.POST, files=request.FILES)
            if profile_form.is_valid():
                try:
                    profile = auth_controller.update_user_profile_from_form(user=request.user, form=profile_form)
                except IntegrityError:
                    request.user.refresh_from_db()
                    profile_form.add_error("email", _("Пользователь с таким email уже зарегистрирован. Укажите другой email."))
                except EmailChangeError as exc:
                    profile_form.add_error("email", exc)
                else:
                    if form_email := pending_email_change_for(request.user):
                        if form_email.email == profile_form.cleaned_data['email']:
                            messages.success(request, email_change_copy('sent'))
                            return redirect('account_email_change')
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
        elif form_action == "staff_deletion_request":
            if not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, _("Это действие доступно только для служебных аккаунтов."))
                return redirect(current_route)
            staff_deletion_form = auth_controller.build_staff_account_deletion_review_form(data=request.POST)
            if staff_deletion_form.is_valid():
                reason = staff_deletion_form.cleaned_data["reason"]
                details = staff_deletion_form.cleaned_data["details"]
                reason_display = dict(staff_deletion_form.fields["reason"].choices).get(reason, reason)
                try:
                    policy = get_active_retention_policy()
                    policy_version = policy.version
                except Exception:
                    policy_version = "v1"

                now = timezone.now()
                with transaction.atomic():
                    deletion, created = AccountDeletionRequest.objects.select_for_update().get_or_create(
                        user=request.user,
                        status=AccountDeletionRequest.Status.HELD,
                        defaults={
                            "hold_code": "STAFF_OFFBOARDING_REVIEW",
                            "policy_version": policy_version,
                            "policy_snapshot": {
                                "reason": reason,
                                "reason_display": str(reason_display),
                                "details": details,
                                "requested_by": request.user.username,
                                "is_staff_offboarding": True,
                                "requested_at": now.isoformat(),
                            },
                        },
                    )
                    if not created:
                        deletion.hold_code = "STAFF_OFFBOARDING_REVIEW"
                        deletion.policy_snapshot = {
                            "reason": reason,
                            "reason_display": str(reason_display),
                            "details": details,
                            "requested_by": request.user.username,
                            "is_staff_offboarding": True,
                            "requested_at": now.isoformat(),
                        }
                        deletion.save(update_fields=["hold_code", "policy_snapshot", "updated_at"])

                try:
                    superadmins = get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=request.user.pk)
                    recipient_emails = [u.email for u in superadmins if u.email]
                    if recipient_emails:
                        subject = f"[KidsMap] Запрос на удаление служебного аккаунта: @{request.user.username}"
                        body = (
                            f"Сотрудник @{request.user.username} ({request.user.get_full_name() or request.user.username}) "
                            f"отправил запрос на удаление/отключение аккаунта.\n\n"
                            f"Причина: {reason_display}\n"
                            f"Комментарий: {details or '—'}\n"
                            f"Дата: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"Для рассмотрения перейдите в профиль сотрудника в админ-панели."
                        )
                        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient_emails, fail_silently=True)
                except Exception:
                    pass

                messages.success(request, _("Müraciətiniz qeydə alındı və baxılmaq üçün administratora göndərildi."))
                return redirect(current_route)
            else:
                messages.error(request, _("Zəhmət olmasa silinmə səbəbini seçin."))
        elif form_action == "cancel_staff_deletion_request":
            if request.user.is_staff or request.user.is_superuser:
                with transaction.atomic():
                    AccountDeletionRequest.objects.filter(
                        user=request.user,
                        status=AccountDeletionRequest.Status.HELD,
                        hold_code="STAFF_OFFBOARDING_REVIEW",
                    ).update(
                        status=AccountDeletionRequest.Status.CANCELED,
                        canceled_at=timezone.now(),
                        hold_code="",
                    )
                messages.success(request, _("Hesabın silinməsi müraciəti ləğv edildi."))
            return redirect(current_route)
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

def _account_deletion_language(request) -> str:
    language = (getattr(request, "LANGUAGE_CODE", None) or "ru").split("-", 1)[0].lower()
    return language if language in {"az", "ru", "en"} else "ru"

def _account_deletion_error_message(code: str) -> str:
    return {
        "retention_policy_not_active": _("Удаление аккаунта временно недоступно до утверждения политики хранения данных."),
        "retention_policy_incomplete": _("Политика хранения данных настроена не полностью."),
        "retention_policy_changed": _("Политика хранения изменилась. Начните запрос заново, чтобы увидеть актуальные условия."),
        "verified_email_required": _("Для удаления аккаунта нужен подтверждённый текущий email."),
        "staff_self_service_forbidden": _("Для служебного аккаунта обратитесь к уполномоченному администратору."),
        "typed_confirmation_invalid": _("Введите фразу подтверждения точно так, как она показана."),
        "confirmation_code_invalid": _("Неверный код подтверждения."),
        "confirmation_attempts_exhausted": _("Лимит попыток исчерпан. Начните запрос заново."),
        "confirmation_code_expired": _("Срок действия кода истёк."),
        "confirmation_code_unavailable": _("Запросите новый код подтверждения."),
        "confirmation_email_failed": _("Не удалось отправить письмо. Повторите попытку позже."),
        "account_deletion_not_cancelable": _("Этот запрос уже нельзя отменить."),
        "cancellation_period_expired": _("Срок отмены запроса истёк."),
        "cancellation_email_unavailable": _("Не удалось отправить код отмены. Обратитесь в поддержку."),
    }.get(code, _("Не удалось выполнить действие. Повторите попытку или обратитесь в поддержку."))

def _deletion_context(
    *,
    deletion=None,
    policy=None,
    language="ru",
    token="",
    form=None,
    code_sent=False,
    staff_blocked=False,
    staff_deletion_form=None,
    pending_staff_deletion=None,
):
    if policy is None and deletion is not None:
        policy = policy_from_request(deletion)
    return {
        "deletion": deletion,
        "deletion_policy": policy,
        "policy_copy": policy.disclosure(language) if policy is not None else {},
        "confirmation_phrase": typed_confirmation_phrase(language),
        "confirmation_code_ttl_minutes": confirmation_code_ttl_minutes(),
        "projected_processing_date": (
            deletion.scheduled_for
            if deletion is not None and deletion.scheduled_for is not None
            else timezone.now() + timedelta(days=policy.grace_period_days)
            if policy is not None
            else None
        ),
        "status_token": token,
        "form": form,
        "code_sent": code_sent,
        "staff_blocked": staff_blocked,
        "staff_deletion_form": staff_deletion_form,
        "pending_staff_deletion": pending_staff_deletion,
        "meta_description": _("Безопасное удаление аккаунта KidsMap и связанных персональных данных."),
    }

def _render_account_deletion(request, template_name, context, *, status=200):
    response = render(request, template_name, context, status=status)
    response["Cache-Control"] = "no-store, max-age=0"
    response["Pragma"] = "no-cache"
    response["Referrer-Policy"] = "origin"
    return response

class AccountDeletionRequestView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")
    template_name = "pages/account_deletion_request.html"

    def get(self, request):
        try:
            policy = get_active_retention_policy()
        except AccountDeletionError:
            policy = None
        form = auth_controller.build_account_deletion_request_form()
        is_staff_user = bool(request.user.is_staff or request.user.is_superuser)
        pending_staff_deletion = None
        if is_staff_user:
            pending_staff_deletion = AccountDeletionRequest.objects.filter(
                user=request.user,
                status=AccountDeletionRequest.Status.HELD,
                hold_code="STAFF_OFFBOARDING_REVIEW",
            ).first()

        return _render_account_deletion(
            request,
            self.template_name,
            _deletion_context(
                policy=policy,
                language=_account_deletion_language(request),
                form=form,
                staff_blocked=is_staff_user,
                staff_deletion_form=auth_controller.build_staff_account_deletion_review_form(),
                pending_staff_deletion=pending_staff_deletion,
            ),
        )

    def post(self, request):
        form_action = (request.POST.get("form_action") or "").strip().lower()
        if form_action == "staff_deletion_request":
            if not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, _("Это действие доступно только для служебных аккаунтов."))
                return redirect("account_settings")
            staff_deletion_form = auth_controller.build_staff_account_deletion_review_form(data=request.POST)
            if staff_deletion_form.is_valid():
                reason = staff_deletion_form.cleaned_data["reason"]
                details = staff_deletion_form.cleaned_data["details"]
                reason_display = dict(staff_deletion_form.fields["reason"].choices).get(reason, reason)
                try:
                    policy = get_active_retention_policy()
                    policy_version = policy.version
                except Exception:
                    policy_version = "v1"

                now = timezone.now()
                with transaction.atomic():
                    deletion, created = AccountDeletionRequest.objects.select_for_update().get_or_create(
                        user=request.user,
                        status=AccountDeletionRequest.Status.HELD,
                        defaults={
                            "hold_code": "STAFF_OFFBOARDING_REVIEW",
                            "policy_version": policy_version,
                            "policy_snapshot": {
                                "reason": reason,
                                "reason_display": str(reason_display),
                                "details": details,
                                "requested_by": request.user.username,
                                "is_staff_offboarding": True,
                                "requested_at": now.isoformat(),
                            },
                        },
                    )
                    if not created:
                        deletion.hold_code = "STAFF_OFFBOARDING_REVIEW"
                        deletion.policy_snapshot = {
                            "reason": reason,
                            "reason_display": str(reason_display),
                            "details": details,
                            "requested_by": request.user.username,
                            "is_staff_offboarding": True,
                            "requested_at": now.isoformat(),
                        }
                        deletion.save(update_fields=["hold_code", "policy_snapshot", "updated_at"])

                try:
                    superadmins = get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=request.user.pk)
                    recipient_emails = [u.email for u in superadmins if u.email]
                    if recipient_emails:
                        subject = f"[KidsMap] Запрос на удаление служебного аккаунта: @{request.user.username}"
                        body = (
                            f"Сотрудник @{request.user.username} ({request.user.get_full_name() or request.user.username}) "
                            f"отправил запрос на удаление/отключение аккаунта.\n\n"
                            f"Причина: {reason_display}\n"
                            f"Комментарий: {details or '—'}\n"
                            f"Дата: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"Для рассмотрения перейдите в профиль сотрудника в админ-панели."
                        )
                        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient_emails, fail_silently=True)
                except Exception:
                    pass

                messages.success(request, _("Müraciətiniz qeydə alındı və baxılmaq üçün administratora göndərildi."))
                return redirect("account_settings")
            else:
                messages.error(request, _("Zəhmət olmasa silinmə səbəbini seçin."))

        language = _account_deletion_language(request)
        form = auth_controller.build_account_deletion_request_form(data=request.POST)
        policy = None
        try:
            policy = get_active_retention_policy()
        except AccountDeletionError as exc:
            form.add_error(None, _account_deletion_error_message(exc.code))
        if policy is not None and form.is_valid():
            try:
                deletion = request_account_deletion(user=request.user, language_code=language)
            except AccountDeletionError as exc:
                form.add_error(None, _account_deletion_error_message(exc.code))
            else:
                return redirect("account_deletion_confirm", subject_reference=deletion.subject_reference)
        return _render_account_deletion(
            request,
            self.template_name,
            _deletion_context(
                policy=policy,
                language=language,
                form=form,
                staff_blocked=request.user.is_staff or request.user.is_superuser,
            ),
            status=400,
        )

class AccountDeletionConfirmView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")
    template_name = "pages/account_deletion_confirm.html"

    def _get_deletion(self, request, subject_reference):
        return get_object_or_404(
            AccountDeletionRequest,
            subject_reference=subject_reference,
            user=request.user,
            status=AccountDeletionRequest.Status.CONFIRMATION_SENT,
        )

    def get(self, request, subject_reference):
        deletion = self._get_deletion(request, subject_reference)
        form = auth_controller.build_account_deletion_confirm_form()
        return _render_account_deletion(
            request,
            self.template_name,
            _deletion_context(deletion=deletion, language=_account_deletion_language(request), form=form),
        )

    def post(self, request, subject_reference):
        deletion = self._get_deletion(request, subject_reference)
        language = _account_deletion_language(request)
        form = auth_controller.build_account_deletion_confirm_form(data=request.POST)
        if form.is_valid():
            try:
                deletion = confirm_account_deletion(
                    user=request.user,
                    code=form.cleaned_data["confirmation_code"],
                    typed_confirmation=form.cleaned_data["typed_confirmation"],
                    language_code=language,
                    http_request=request,
                )
            except AccountDeletionError as exc:
                field = "typed_confirmation" if exc.code == "typed_confirmation_invalid" else "confirmation_code"
                if exc.code not in {
                    "typed_confirmation_invalid",
                    "confirmation_code_invalid",
                    "confirmation_attempts_exhausted",
                    "confirmation_code_expired",
                    "confirmation_code_unavailable",
                }:
                    field = None
                form.add_error(field, _account_deletion_error_message(exc.code))
            else:
                token = make_status_token(deletion.subject_reference)
                url = reverse("account_deletion_status", args=[deletion.subject_reference])
                return redirect(f"{url}?{urlencode({'token': token})}")
        return _render_account_deletion(
            request,
            self.template_name,
            _deletion_context(deletion=deletion, language=language, form=form),
            status=400,
        )

def account_deletion_status(request, subject_reference):
    token = request.GET.get("token", "")
    if not verify_status_token(subject_reference, token):
        raise Http404
    deletion = get_object_or_404(AccountDeletionRequest, subject_reference=subject_reference)
    return _render_account_deletion(
        request,
        "pages/account_deletion_status.html",
        _deletion_context(deletion=deletion, language=_account_deletion_language(request), token=token),
    )

def account_deletion_cancel(request, subject_reference):
    token = request.GET.get("token", "") or request.POST.get("status_token", "")
    if not verify_status_token(subject_reference, token):
        raise Http404
    deletion = get_object_or_404(AccountDeletionRequest, subject_reference=subject_reference)
    language = _account_deletion_language(request)
    code_sent = deletion.code_purpose == AccountDeletionRequest.CodePurpose.CANCEL
    if request.method == "POST":
        form = auth_controller.build_account_deletion_cancel_form(data=request.POST)
        if form.is_valid():
            action = form.cleaned_data["form_action"]
            try:
                if action == "send_code":
                    deletion = issue_cancellation_code(subject_reference=subject_reference, language_code=language)
                    code_sent = True
                else:
                    deletion = cancel_account_deletion(
                        subject_reference=subject_reference,
                        code=form.cleaned_data["confirmation_code"],
                    )
                    url = reverse("account_deletion_status", args=[deletion.subject_reference])
                    return redirect(f"{url}?{urlencode({'token': token})}")
            except AccountDeletionError as exc:
                field = "confirmation_code" if action == "cancel" else None
                form.add_error(field, _account_deletion_error_message(exc.code))
        response_status = 400 if form.errors else 200
    else:
        form = auth_controller.build_account_deletion_cancel_form(form_action="send_code")
        response_status = 200
    return _render_account_deletion(
        request,
        "pages/account_deletion_cancel.html",
        _deletion_context(deletion=deletion, language=language, token=token, form=form, code_sent=code_sent),
        status=response_status,
    )

def account_deletion_request(request):
    return AccountDeletionRequestView.as_view()(request)

def account_deletion_confirm(request, subject_reference):
    return AccountDeletionConfirmView.as_view()(request, subject_reference=subject_reference)

def account_register(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    auth_intent = _resolve_auth_intent(request)
    language = (request.LANGUAGE_CODE or "az").split("-")[0]
    form = auth_controller.build_registration_form(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = auth_controller.register_user_from_form(form=form)
        except IntegrityError:
            form.add_error("email", _("Пользователь с таким email уже зарегистрирован. Войдите в аккаунт или используйте другой email."))
            return render(request, "auth/register.html", {
                "form": form,
                "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
                "auth_intent": auth_intent,
            })
        verification = auth_controller.send_registration_verification_code(
            user=user,
            email=form.cleaned_data["email"],
        )
        if verification.ok:
            success_message = {
                "az": "Qeydiyyat demək olar ki, tamamlandı. E-poçta göndərilən kodu daxil edib hesabınızı təsdiqləyin.",
                "en": "Registration is almost complete. Enter the code from your email to confirm your account.",
            }.get(language, _("Регистрация почти завершена. Введите код из письма для подтверждения email."))
            messages.success(
                request,
                success_message,
            )
        else:
            messages.error(request, verification.message)
        query = urlencode(
            {
                "email": form.cleaned_data["email"],
                "next": _resolve_safe_next_url(request, reverse("account_profile")),
                "intent": auth_intent,
            }
        )
        return redirect(f"{reverse('account_verify_email')}?{query}")

    return render(
        request,
        "auth/register.html",
        {
            "form": form,
            "meta_description": {
                "az": "KidsMap qeydiyyatı: hesab yaradın və kataloqdan rahat istifadə etməyə başlayın.",
                "en": "Register on KidsMap and start using the catalog.",
            }.get(language, _("Регистрация в KidsMap: создайте аккаунт и начните пользоваться каталогом.")),
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
            "auth_intent": auth_intent,
            "analytics_events": [
                {
                    "name": FunnelEvent.EVENT_ADD_PLACE_SIGNUP_START,
                    "params": {"page_type": "add_place_signup", "intent": auth_intent},
                }
            ]
            if auth_intent == AUTH_INTENT_ADD_PLACE
            else [],
        },
    )

def account_login(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    auth_intent = _resolve_auth_intent(request)
    language = (request.LANGUAGE_CODE or "az").split("-")[0]
    form = auth_controller.build_login_form(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        if form.cleaned_data.get("remember_me"):
            request.session.set_expiry(int(getattr(settings, "SESSION_COOKIE_AGE", 1209600)))
        else:
            request.session.set_expiry(0)
        if language == "az":
            messages.success(request, "Hesabınıza daxil oldunuz.")
        elif language == "en":
            messages.success(request, "You are now signed in.")
        else:
            messages.success(request, _("Вы вошли в аккаунт."))
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    if language == "az":
        meta_description = "KidsMap hesabınıza daxil olun."
    elif language == "en":
        meta_description = "Sign in to your KidsMap account."
    else:
        meta_description = _("Вход в аккаунт KidsMap.")

    return render(
        request,
        "auth/login.html",
        {
            "form": form,
            "meta_description": meta_description,
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
            "auth_intent": auth_intent,
        },
    )

@require_POST
def account_logout(request):
    auth_logout(request)
    messages.info(request, _("Вы вышли из аккаунта."))
    return redirect(reverse("home"))

class UserPasswordResetView(auth_views.PasswordResetView):
    template_name = "auth/password_reset_form.html"
    email_template_name = "auth/password_reset_email.txt"
    html_email_template_name = "auth/password_reset_email.html"
    subject_template_name = "auth/password_reset_subject.txt"
    form_class = UserPasswordResetForm
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        opts = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
        }
        form.save(**opts)
        is_ajax = (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.POST.get("is_ajax") == "1"
            or "application/json" in self.request.headers.get("accept", "")
        )
        if is_ajax:
            language = (getattr(self.request, "LANGUAGE_CODE", None) or "az").split("-")[0]
            if language == "az":
                msg = "Şifrənin bərpası üçün təlimat e-poçt ünvanınıza göndərildi."
            elif language == "en":
                msg = "Password reset instructions have been sent to your email."
            else:
                msg = "Письмо со ссылкой для смены пароля отправлено на ваш email."
            return JsonResponse({"ok": True, "message": msg})
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        is_ajax = (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.POST.get("is_ajax") == "1"
            or "application/json" in self.request.headers.get("accept", "")
        )
        if is_ajax:
            error_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_list.append(str(error))
            msg = error_list[0] if error_list else _("Проверьте введенные данные.")
            return JsonResponse(
                {
                    "ok": False,
                    "errors": form.errors.get_json_data(),
                    "error_list": error_list,
                    "message": msg,
                },
                status=400,
            )
        return super().form_invalid(form)
