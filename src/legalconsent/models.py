from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(_("Сохранённая запись не редактируется."))


class AppendOnlyRecord(models.Model):
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self._state.adding or force_update or update_fields is not None:
            raise ValidationError(_("Сохранённая запись не редактируется."))
        return super().save(force_insert=True, using=using)


class LegalDocumentSnapshot(AppendOnlyRecord):
    """The localized text presented at acceptance, independent of later site settings."""

    slug = models.SlugField(_("Документ"), max_length=32)
    language = models.CharField(_("Язык"), max_length=8)
    version = models.CharField(_("Версия"), max_length=40)
    generation = models.PositiveIntegerField(_("Поколение согласия"))
    title = models.CharField(_("Название"), max_length=255)
    published_on = models.DateField(_("Дата публикации"))
    updated_on = models.DateField(_("Дата изменения документа"))
    fingerprint = models.CharField(_("SHA-256 редакции"), max_length=64, unique=True)
    content = models.JSONField(_("Текст и реквизиты документа"))

    class Meta:
        verbose_name = _("Сохранённая редакция")
        verbose_name_plural = _("Сохранённые редакции")
        default_permissions = ("view",)

    def __str__(self):
        return f"{self.title} · {self.version} · {self.language.upper()}"


class LegalAcceptance(AppendOnlyRecord):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("Пользователь"), on_delete=models.CASCADE)
    document = models.ForeignKey(LegalDocumentSnapshot, verbose_name=_("Редакция"), on_delete=models.PROTECT)
    accepted_at = models.DateTimeField(_("Дата согласия"), auto_now_add=True)

    class Meta:
        verbose_name = _("Согласие пользователя")
        verbose_name_plural = _("Согласия пользователей")
        default_permissions = ("view",)
        constraints = [
            models.UniqueConstraint(fields=("user", "document"), name="legal_acceptance_user_snapshot_unique"),
        ]

    def __str__(self):
        return f"{self.user_id} · {self.document}"
