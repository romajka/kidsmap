from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from catalog.models import SEOAuditRun, SEOChange, SEOIssue
from catalog.services.seo_fix_engine import SEOFixEngine


@admin.register(SEOAuditRun)
class SEOAuditRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "audit_type",
        "status_badge",
        "total_urls",
        "error_count",
        "warning_count",
        "auto_fix_count",
        "started_at",
        "finished_at",
    )
    list_filter = ("audit_type", "status", "environment")
    readonly_fields = (
        "started_at",
        "finished_at",
        "audit_type",
        "total_urls",
        "error_count",
        "warning_count",
        "auto_fix_count",
        "status",
        "code_version",
        "environment",
        "summary_notes",
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "run-audit-now/",
                self.admin_site.admin_view(self.run_audit_now_view),
                name="catalog_seoauditrun_run_now",
            ),
            path(
                "apply-fixes-now/",
                self.admin_site.admin_view(self.apply_fixes_now_view),
                name="catalog_seoauditrun_apply_fixes_now",
            ),
            path(
                "clear-history-now/",
                self.admin_site.admin_view(self.clear_history_now_view),
                name="catalog_seoauditrun_clear_history_now",
            ),
        ]
        return custom_urls + urls

    def run_audit_now_view(self, request):
        from catalog.services.seo_audit_engine import SEOAuditEngine
        try:
            engine = SEOAuditEngine(environment="admin_trigger")
            run = engine.run_audit()
            messages.success(
                request,
                f"🚀 SEO-аудит успешно выполнен (Запуск #{run.pk})! "
                f"Проверено {run.total_urls} URL. Найдено ошибок: {run.error_count}, предупреждений: {run.warning_count}."
            )
        except Exception as exc:
            messages.error(request, f"Ошибка выполнения SEO-аудита: {exc}")

        from django.shortcuts import redirect
        return redirect("admin:catalog_seoauditrun_changelist")

    def apply_fixes_now_view(self, request):
        from catalog.services.seo_fix_engine import SEOFixEngine
        try:
            engine = SEOFixEngine()
            changes = engine.apply_safe_fixes(dry_run=False)
            if changes:
                messages.success(request, f"⚡ Успешно применено {len(changes)} безопасных автоисправлений Level A!")
            else:
                messages.info(request, "⚡ Нет открытых проблем Level A — все автоисправления уже применены.")
        except Exception as exc:
            messages.error(request, f"Ошибка применения автоисправлений: {exc}")

        from django.shortcuts import redirect
        return redirect("admin:catalog_seoauditrun_changelist")

    def clear_history_now_view(self, request):
        try:
            runs_count = SEOAuditRun.objects.count()
            issues_count = SEOIssue.objects.count()
            SEOAuditRun.objects.all().delete()
            SEOIssue.objects.filter(audit_run__isnull=True).delete()
            messages.success(
                request,
                f"🗑 История прошлых аудитов успешно очищена ({runs_count} запусков, {issues_count} проблем)."
            )
        except Exception as exc:
            messages.error(request, f"Ошибка очистки истории: {exc}")

        from django.shortcuts import redirect
        return redirect("admin:catalog_seoauditrun_changelist")

    def status_badge(self, obj):
        color = "green" if obj.status == "completed" else "red" if obj.status == "failed" else "orange"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = _("Статус")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SEOIssue)
class SEOIssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "level_badge",
        "severity_badge",
        "status_badge",
        "issue_code",
        "url",
        "page_type",
        "language",
        "detected_at",
    )
    list_filter = ("level", "severity", "status", "page_type", "language", "is_auto_fixable", "requires_approval")
    search_fields = ("url", "issue_code", "description", "current_value", "proposed_value")
    readonly_fields = (
        "audit_run",
        "url",
        "page_type",
        "language",
        "issue_code",
        "level",
        "severity",
        "description",
        "current_value",
        "detected_at",
        "last_checked_at",
        "place",
    )
    actions = ["approve_selected_proposals", "reject_selected_proposals", "recheck_selected_issues"]

    def level_badge(self, obj):
        color = "#28a745" if obj.level == "A" else "#fd7e14" if obj.level == "B" else "#dc3545"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">Level {}</span>',
            color,
            obj.level,
        )
    level_badge.short_description = _("Уровень")

    def severity_badge(self, obj):
        color = "#dc3545" if obj.severity == "critical" else "#ffc107" if obj.severity == "warning" else "#17a2b8"
        text_color = "black" if obj.severity == "warning" else "white"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_severity_display(),
        )
    severity_badge.short_description = _("Важность")

    def status_badge(self, obj):
        color = "green" if obj.status in ("approved", "fixed", "resolved") else "red" if obj.status == "rejected" else "orange"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = _("Статус")

    @admin.action(description=_("Утвердить выбранные предложения (Level B)"))
    def approve_selected_proposals(self, request, queryset):
        approved_count = 0
        for issue in queryset.filter(level=SEOIssue.LEVEL_B, status=SEOIssue.STATUS_OPEN):
            issue.status = SEOIssue.STATUS_APPROVED
            issue.save(update_fields=["status"])
            approved_count += 1
        self.message_user(request, f"Утверждено {approved_count} предложений Level B.", messages.SUCCESS)

    @admin.action(description=_("Отклонить выбранные предложения"))
    def reject_selected_proposals(self, request, queryset):
        rejected_count = 0
        for issue in queryset.filter(status=SEOIssue.STATUS_OPEN):
            issue.status = SEOIssue.STATUS_REJECTED
            issue.save(update_fields=["status"])
            rejected_count += 1
        self.message_user(request, f"Отклонено {rejected_count} проблем/предложений.", messages.WARNING)

    @admin.action(description=_("Повторно проверить статус выбранных проблем"))
    def recheck_selected_issues(self, request, queryset):
        from catalog.services.seo_fix_engine import SEOFixEngine
        engine = SEOFixEngine()
        checked_count = 0
        for issue in queryset:
            res = engine._recheck_issue_url(issue)
            checked_count += 1
        self.message_user(request, f"Повторно проверено {checked_count} URL.", messages.INFO)


@admin.register(SEOChange)
class SEOChangeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "change_summary",
        "source",
        "is_reversible",
        "rollback_badge",
        "applied_at",
        "recheck_result",
    )
    list_filter = ("is_reversible", "is_rolled_back", "source")
    search_fields = ("change_summary", "old_value", "new_value", "reason")
    readonly_fields = (
        "issue",
        "change_summary",
        "old_value",
        "new_value",
        "reason",
        "source",
        "applied_at",
        "recheck_result",
        "is_reversible",
        "is_rolled_back",
        "rolled_back_at",
    )
    actions = ["rollback_selected_changes"]

    def rollback_badge(self, obj):
        if obj.is_rolled_back:
            return format_html('<span style="color: red; font-weight: bold;">Откачено ({})</span>', obj.rolled_back_at.strftime('%Y-%m-%d')) if obj.rolled_back_at else "Откачено"
        return format_html('<span style="color: green;">Активно</span>')
    rollback_badge.short_description = _("Статус отката")

    @admin.action(description=_("Откатить выбранные изменения SEO"))
    def rollback_selected_changes(self, request, queryset):
        engine = SEOFixEngine()
        success_count = 0
        for change in queryset.filter(is_rolled_back=False, is_reversible=True):
            try:
                engine.rollback_change(change.pk)
                success_count += 1
            except Exception as exc:
                self.message_user(request, f"Ошибка отката #{change.pk}: {exc}", messages.ERROR)
        if success_count:
            self.message_user(request, f"Успешно откачено {success_count} изменений.", messages.SUCCESS)

    def has_add_permission(self, request):
        return False
