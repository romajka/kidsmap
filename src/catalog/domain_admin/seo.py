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
        "view_report_button",
    )
    list_filter = ("audit_type", "status", "environment")
    readonly_fields = (
        "formatted_report_html",
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

    def view_report_button(self, obj):
        from django.urls import reverse
        url = reverse("admin:catalog_seoissue_changelist") + f"?audit_run__id__exact={obj.id}"
        total_issues = obj.error_count + obj.warning_count
        btn_color = "#2563eb" if total_issues > 0 else "#64748b"
        return format_html(
            '<a class="button" style="background-color: {}; color: #ffffff; padding: 5px 12px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;" href="{}">👁 Смотреть отчёт ({})</a>',
            btn_color,
            url,
            total_issues,
        )
    view_report_button.short_description = _("Отчёт и проблемы")

    def formatted_report_html(self, obj):
        if not obj or not obj.pk:
            return ""

        from django.urls import reverse
        issues_url = reverse("admin:catalog_seoissue_changelist") + f"?audit_run__id__exact={obj.id}"
        issues_list = obj.issues.all()[:50]

        issues_rows_html = ""
        for issue in issues_list:
            level_bg = "#22c55e" if issue.level == "A" else "#f97316" if issue.level == "B" else "#ef4444"
            sev_bg = "#dc2626" if issue.severity == "critical" else "#f59e0b"
            issues_rows_html += f"""
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 8px 10px;"><span style="background: {level_bg}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 700;">Level {issue.level}</span></td>
                <td style="padding: 8px 10px;"><span style="background: {sev_bg}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{issue.get_severity_display()}</span></td>
                <td style="padding: 8px 10px; font-family: monospace; font-size: 12px; font-weight: 600;">{issue.issue_code}</td>
                <td style="padding: 8px 10px;"><a href="{issue.url}" target="_blank" style="color: #2563eb; text-decoration: underline;">{issue.url}</a></td>
                <td style="padding: 8px 10px; font-size: 13px; color: #334155;">{issue.description}</td>
            </tr>
            """

        if not issues_rows_html:
            issues_rows_html = '<tr><td colspan="5" style="padding: 16px; text-align: center; color: #166534; font-weight: 600;">🎉 Ошибок не обнаружено! Все проверенные URL в идеальном порядке.</td></tr>'

        return format_html(
            f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 14px; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #0f172a;">📊 Отчёт аудита #{obj.id}</h3>
                        <span style="font-size: 13px; color: #64748b;">Тип: {obj.get_audit_type_display()} | Статус: {obj.get_status_display()}</span>
                    </div>
                    <a href="{issues_url}" style="background-color: #2563eb; color: #ffffff; font-weight: 600; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-size: 13px;">
                        🔍 Открыть список проблем ({obj.error_count + obj.warning_count})
                    </a>
                </div>

                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
                        <div style="font-size: 12px; color: #64748b; font-weight: 600;">ПРОВЕРЕНО URL</div>
                        <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{obj.total_urls}</div>
                    </div>
                    <div style="background: #fef2f2; padding: 12px; border-radius: 8px; border: 1px solid #fecaca; text-align: center;">
                        <div style="font-size: 12px; color: #991b1b; font-weight: 600;">ОШИБОК</div>
                        <div style="font-size: 22px; font-weight: 800; color: #dc2626;">{obj.error_count}</div>
                    </div>
                    <div style="background: #fff7ed; padding: 12px; border-radius: 8px; border: 1px solid #fed7aa; text-align: center;">
                        <div style="font-size: 12px; color: #9a3412; font-weight: 600;">ПРЕДУПРЕЖДЕНИЙ</div>
                        <div style="font-size: 22px; font-weight: 800; color: #d97706;">{obj.warning_count}</div>
                    </div>
                    <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; border: 1px solid #bbf7d0; text-align: center;">
                        <div style="font-size: 12px; color: #166534; font-weight: 600;">АВТОИСПРАВЛЕНИЙ</div>
                        <div style="font-size: 22px; font-weight: 800; color: #16a34a;">{obj.auto_fix_count}</div>
                    </div>
                </div>

                <h4 style="margin: 0 0 10px 0; font-size: 15px; font-weight: 700; color: #1e293b;">Выявленные замечания:</h4>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: #f1f5f9; color: #475569; font-weight: 700;">
                                <th style="padding: 8px 10px;">Уровень</th>
                                <th style="padding: 8px 10px;">Важность</th>
                                <th style="padding: 8px 10px;">Код</th>
                                <th style="padding: 8px 10px;">URL</th>
                                <th style="padding: 8px 10px;">Описание</th>
                            </tr>
                        </thead>
                        <tbody>
                            {issues_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
            """
        )
    formatted_report_html.short_description = _("Наглядный отчёт аудита")

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
        "url_link",
        "edit_object_button",
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

    def url_link(self, obj):
        if not obj.url:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" style="color: #2563eb; font-weight: 600; text-decoration: underline; display: inline-flex; align-items: center; gap: 4px;">🌐 {} ↗</a>',
            obj.url,
            obj.url,
        )
    url_link.short_description = _("URL страницы")

    def edit_object_button(self, obj):
        from django.urls import reverse
        if obj.place_id:
            edit_url = reverse("admin:catalog_place_change", args=[obj.place_id])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #059669; color: #ffffff; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">✏️ Редактировать карточку #{place_id}</a>',
                edit_url,
                place_id=obj.place_id,
            )
        elif obj.page_type == "static" or "contacts" in obj.url or "about" in obj.url:
            edit_url = reverse("admin:catalog_catalogcontentsettings_changelist")
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #475569; color: #ffffff; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">⚙️ Редактировать настройки</a>',
                edit_url,
            )
        return format_html('<span style="color: #94a3b8; font-size: 12px;">—</span>')
    edit_object_button.short_description = _("Быстрое редактирование")

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
