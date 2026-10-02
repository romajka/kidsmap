"""Shared, settings-backed moderation SLA calculation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


@dataclass(frozen=True, slots=True)
class SlaState:
    content_type: str
    status: str
    submitted_at: object
    deadline: object | None
    elapsed_seconds: int
    remaining_seconds: int | None
    percentage: int | None


def _policy(content_type: str) -> dict:
    policies = getattr(settings, "MODERATION_SLA", {})
    if not isinstance(policies, dict):
        raise ValueError('Invalid moderation SLA policy container')
    policy = policies.get(content_type)
    if policy is None and content_type in {"organization", "program", "activity", "offering_group", "affiliation"}:
        policy = policies.get("place")
    if not isinstance(policy, dict):
        raise ValueError(f"Unsupported moderation SLA content type: {content_type}")
    try:
        hours = int(policy["hours"])
        warning = int(policy["warning_percent"])
        critical = int(policy["critical_percent"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid moderation SLA policy: {content_type}") from exc
    if hours < 1 or not 0 < warning < critical < 100:
        raise ValueError(f"Invalid moderation SLA policy: {content_type}")
    return {"seconds": hours * 3600, "warning": warning, "critical": critical}


def calculate_sla(content_type: str, submitted_at, *, paused_at=None, completed_at=None, now=None) -> SlaState:
    policy = _policy(content_type)
    now = now or timezone.now()
    if paused_at is not None:
        elapsed = max(0, int((paused_at - submitted_at).total_seconds())) if submitted_at else 0
        return SlaState(content_type, "paused", submitted_at, None, elapsed, None, None)
    if submitted_at is None:
        return SlaState(content_type, 'unknown', None, None, 0, None, None)
    elapsed = max(0, int(((completed_at or now) - submitted_at).total_seconds()))
    total = policy["seconds"]
    remaining = total - elapsed
    percentage = int((elapsed * 100) / total)
    deadline = submitted_at + timedelta(seconds=total)
    if completed_at:
        status = 'completed'
    elif elapsed >= total:
        status = "breached"
    elif elapsed * 100 >= total * policy["critical"]:
        status = "critical"
    elif percentage >= policy["warning"]:
        status = "warning"
    else:
        status = "fresh"
    return SlaState(content_type, status, submitted_at, deadline, elapsed, remaining, percentage)


def prepare_moderation_save(instance, kwargs, *, previous=None, terminal=('approved', 'rejected', 'declined', 'published')):
    """Maintain lifecycle dates without restarting clocks on ordinary edits.

    Bulk queryset updates must set metadata explicitly; no hidden model signal.
    """
    fields = kwargs.get('update_fields')
    if fields is not None and 'status' not in fields:
        return
    if previous is None and instance.pk:
        previous = type(instance).objects.filter(pk=instance.pk).first()
    old_status = previous.status if previous else None
    now = timezone.now()
    changed = set()
    def assign(field, value):
        if hasattr(instance, field):
            setattr(instance, field, value)
            changed.add(field)
    if instance.status == 'pending':
        if old_status != 'pending':
            assign('submitted_at', instance.submitted_at if previous is None and instance.submitted_at else now)
            assign('needs_changes_at', None)
            assign('moderated_at', None)
            assign('moderated_by', None)
        elif not instance.submitted_at:
            assign('submitted_at', instance.created_at or now)
    elif old_status != instance.status:
        if instance.status == 'needs_changes' or (instance._meta.model_name == 'volunteerplacerevision' and instance.status == 'rejected'):
            assign('needs_changes_at', now)
        if previous and old_status == 'pending' and (instance.status in terminal or instance.status == 'needs_changes'):
            assign('moderated_at', now)
    if fields is not None:
        kwargs['update_fields'] = set(fields) | changed


def submission_message(content_type):
    from catalog.services.permanent_place_rules import copy as t
    from django.utils.translation import gettext
    hours = _policy(content_type)['seconds'] // 3600
    rules = t('правилам сообщества, требованиям к отзывам и политике конфиденциальности', 'icma qaydalarına, rəy tələblərinə və məxfilik siyasətinə', 'community rules, review requirements and privacy policy') if content_type == 'review' else t('требованиям KidsMap', 'KidsMap tələblərinə', 'KidsMap requirements')
    receipt = gettext('Мы получили ваш отзыв. Он появится на сайте после проверки модератором.') + ' ' if content_type == 'review' else ''
    return receipt + t('На модерации. Рассмотрим материал в течение {hours} календарных часов на соответствие {rules}. Это срок рассмотрения, не гарантия публикации. Результат: публикация, отклонение или доработка.', 'Moderasiyadadır. Materialı {hours} təqvim saatı ərzində {rules} uyğunluq baxımından yoxlayacağıq. Bu baxılma müddətidir, yayımlanma zəmanəti deyil. Nəticə: yayımlanma, rədd və ya düzəliş.', 'On moderation. We will review the material within {hours} calendar hours for compliance with {rules}. This is a review deadline, not a publication guarantee. The outcome may be publication, rejection or requested changes.').format(hours=hours, rules=rules)
