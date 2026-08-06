from django.db import models
from django.utils.translation import gettext_lazy as _


class SEOAuditRun(models.Model):
    AUDIT_TYPE_FULL = "full"
    AUDIT_TYPE_TECHNICAL = "technical"
    AUDIT_TYPE_CONTENT = "content"
    AUDIT_TYPE_SCHEMA = "schema"
    AUDIT_TYPE_LINKS = "links"
    AUDIT_TYPE_SITEMAP = "sitemap"

    AUDIT_TYPE_CHOICES = [
        (AUDIT_TYPE_FULL, _("Полный аудит")),
        (AUDIT_TYPE_TECHNICAL, _("Технический аудит")),
        (AUDIT_TYPE_CONTENT, _("Контентный аудит")),
        (AUDIT_TYPE_SCHEMA, _("Аудит Schema.org")),
        (AUDIT_TYPE_LINKS, _("Аудит внутренних ссылок")),
        (AUDIT_TYPE_SITEMAP, _("Аудит Sitemap")),
    ]

    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_RUNNING, _("Выполняется")),
        (STATUS_COMPLETED, _("Завершён")),
        (STATUS_FAILED, _("Ошибка")),
    ]

    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата начала"))
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Дата завершения"))
    audit_type = models.CharField(
        max_length=30,
        choices=AUDIT_TYPE_CHOICES,
        default=AUDIT_TYPE_FULL,
        verbose_name=_("Тип проверки"),
    )
    total_urls = models.PositiveIntegerField(default=0, verbose_name=_("Проверено URL"))
    error_count = models.PositiveIntegerField(default=0, verbose_name=_("Ошибок"))
    warning_count = models.PositiveIntegerField(default=0, verbose_name=_("Предупреждений"))
    auto_fix_count = models.PositiveIntegerField(default=0, verbose_name=_("Автоисправлений"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RUNNING,
        verbose_name=_("Статус"),
    )
    code_version = models.CharField(max_length=100, blank=True, verbose_name=_("Версия кода"))
    environment = models.CharField(max_length=50, default="production", verbose_name=_("Окружение"))
    summary_notes = models.TextField(blank=True, verbose_name=_("Заметки и итоги"))

    class Meta:
        verbose_name = _("Запуск SEO-аудита")
        verbose_name_plural = _("Запуски SEO-аудитов")
        ordering = ["-started_at"]

    def __str__(self):
        return f"SEO Audit #{self.pk} [{self.audit_type}] - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class SEOIssue(models.Model):
    LEVEL_A = "A"
    LEVEL_B = "B"
    LEVEL_C = "C"

    LEVEL_CHOICES = [
        (LEVEL_A, _("Level A (Safe Auto-Fix)")),
        (LEVEL_B, _("Level B (Draft / Approval Required)")),
        (LEVEL_C, _("Level C (Manual Review Only)")),
    ]

    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    SEVERITY_CHOICES = [
        (SEVERITY_CRITICAL, _("Критическая")),
        (SEVERITY_WARNING, _("Предупреждение")),
        (SEVERITY_INFO, _("Информирование")),
    ]

    STATUS_OPEN = "open"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_FIXED = "fixed"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = [
        (STATUS_OPEN, _("Открыта")),
        (STATUS_APPROVED, _("Утверждена")),
        (STATUS_REJECTED, _("Отклонена")),
        (STATUS_FIXED, _("Исправлена")),
        (STATUS_RESOLVED, _("Решена")),
    ]

    audit_run = models.ForeignKey(
        SEOAuditRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
        verbose_name=_("Запуск аудита"),
    )
    url = models.CharField(max_length=1000, verbose_name=_("URL страницы"))
    page_type = models.CharField(max_length=50, default="other", verbose_name=_("Тип страницы"))
    language = models.CharField(max_length=10, default="all", verbose_name=_("Язык"))
    issue_code = models.CharField(max_length=100, db_index=True, verbose_name=_("Код проблемы"))
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_WARNING,
        verbose_name=_("Важность"),
    )
    level = models.CharField(
        max_length=5,
        choices=LEVEL_CHOICES,
        default=LEVEL_A,
        verbose_name=_("Уровень автоматизации"),
    )
    description = models.TextField(verbose_name=_("Описание"))
    current_value = models.TextField(blank=True, verbose_name=_("Текущее значение"))
    proposed_value = models.TextField(blank=True, verbose_name=_("Предлагаемое значение"))
    rationale = models.TextField(blank=True, verbose_name=_("Причина / Обоснование"))
    expected_impact = models.TextField(blank=True, verbose_name=_("Ожидаемый эффект"))
    risk_assessment = models.TextField(blank=True, verbose_name=_("Оценка риска"))
    rollback_instructions = models.TextField(blank=True, verbose_name=_("Способ отката"))
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата обнаружения"))
    last_checked_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата последней проверки"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        verbose_name=_("Статус"),
    )
    is_auto_fixable = models.BooleanField(default=False, verbose_name=_("Авто-исправление (Level A)"))
    requires_approval = models.BooleanField(default=False, verbose_name=_("Требует подтверждения (Level B)"))
    place = models.ForeignKey(
        "catalog.Place",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seo_issues",
        verbose_name=_("Связанное заведение"),
    )

    class Meta:
        verbose_name = _("SEO-проблема")
        verbose_name_plural = _("SEO-проблемы")
        ordering = ["-detected_at"]

    def __str__(self):
        return f"[{self.level}][{self.severity}] {self.issue_code} @ {self.url}"


class SEOChange(models.Model):
    issue = models.ForeignKey(
        SEOIssue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changes",
        verbose_name=_("Связанная SEO-проблема"),
    )
    change_summary = models.CharField(max_length=500, verbose_name=_("Что изменено"))
    old_value = models.TextField(blank=True, verbose_name=_("Старое значение"))
    new_value = models.TextField(blank=True, verbose_name=_("Новое значение"))
    reason = models.TextField(blank=True, verbose_name=_("Причина"))
    source = models.CharField(max_length=50, default="safe_auto_fix", verbose_name=_("Источник изменения"))
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата изменения"))
    recheck_result = models.CharField(max_length=200, blank=True, verbose_name=_("Результат повторной проверки"))
    is_reversible = models.BooleanField(default=True, verbose_name=_("Возможность отката"))
    is_rolled_back = models.BooleanField(default=False, verbose_name=_("Откачено"))
    rolled_back_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Дата отката"))

    class Meta:
        verbose_name = _("Запись изменения SEO")
        verbose_name_plural = _("Записи изменений SEO")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"SEOChange #{self.pk}: {self.change_summary} ({self.applied_at.strftime('%Y-%m-%d %H:%M')})"
