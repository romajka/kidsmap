from __future__ import annotations

import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from catalog.models import (
    CatalogContentSettings,
    Place,
    PlacePhoto,
    PlaceScheduleDay,
    PlaceScheduleInterval,
)
from catalog.services.content_quality import public_place_queryset
from catalog.services.indexnow import (
    enqueue_indexnow_urls,
    indexnow_enabled,
    place_canonical_urls,
    seo_landing_canonical_urls,
)
from catalog.services.seo_landing_visibility import build_seo_landing_visibility


logger = logging.getLogger(__name__)


SIGNIFICANT_PLACE_FIELDS = frozenset(
    {
        "slug",
        "name",
        "name_az",
        "name_ru",
        "name_en",
        "description_az",
        "description_ru",
        "description_en",
        "category_id",
        "category",
        "subcategory_id",
        "subcategory",
        "age_from",
        "age_to",
        "age_open_ended",
        "offers_adult_classes",
        "district",
        "metro",
        "address",
        "phone1",
        "phone2",
        "phone3",
        "cover_photo",
        "photo",
        "instagram",
        "website",
        "schedule",
        "schedule_mode",
        "schedule_note_az",
        "schedule_note_ru",
        "schedule_note_en",
        "lesson_duration_minutes",
        "lesson_format",
        "lessons_per_week",
        "lessons_per_month",
        "pricing_plans",
        "is_temporary",
        "temporary_start",
        "temporary_end",
        "lat",
        "lng",
        "price_from",
        "price_to",
        "price_per_lesson",
        "price_per_month",
        "price_per_8_lessons",
        "extra_conditions",
        "additional_info",
        "extra_conditions_az",
        "extra_conditions_ru",
        "extra_conditions_en",
        "additional_info_az",
        "additional_info_ru",
        "additional_info_en",
        "rating_avg",
        "rating_count",
        "is_active",
        "is_verified",
        "status",
        "last_verified_at",
        "published_at",
        "deleted_at",
    }
)


def _place_is_indexable(place_id: int) -> bool:
    return public_place_queryset(Place.objects.filter(pk=place_id)).exists()


def _field_value(place: Place, field_name: str):
    value = getattr(place, field_name)
    return getattr(value, "name", value)


def _significant_snapshot(place: Place) -> dict:
    return {
        field_name: _field_value(place, field_name)
        for field_name in SIGNIFICANT_PLACE_FIELDS
    }


def _indexable_seo_landing_urls() -> list[str]:
    visibility = build_seo_landing_visibility(CatalogContentSettings.get_solo())
    urls: list[str] = []
    for slug in visibility.indexable_slugs:
        urls.extend(seo_landing_canonical_urls(slug))
    return urls


def _safely_run(callback, *args, **kwargs) -> None:
    try:
        callback(*args, **kwargs)
    except Exception:
        logger.exception("IndexNow change notification failed")


def _notify_indexable_seo_landings() -> None:
    enqueue_indexnow_urls(_indexable_seo_landing_urls())


def _notify_place_change(
    *,
    place_id: int,
    previous_slug: str,
    previously_indexable: bool,
    should_notify_current: bool,
) -> None:
    place = Place.objects.filter(pk=place_id).first()
    currently_indexable = bool(place and _place_is_indexable(place_id))
    urls: list[str] = []

    if previously_indexable and (
        not currently_indexable or (place and previous_slug != place.slug)
    ):
        url_source = place or Place(pk=place_id, slug=previous_slug, name="removed")
        urls.extend(place_canonical_urls(url_source, slug=previous_slug))

    if place and currently_indexable and should_notify_current:
        urls.extend(place_canonical_urls(place))

    if should_notify_current or previously_indexable != currently_indexable:
        urls.extend(_indexable_seo_landing_urls())

    if urls:
        enqueue_indexnow_urls(urls)


@receiver(pre_save, sender=Place, dispatch_uid="indexnow_capture_place_state")
def capture_place_indexnow_state(sender, instance, **kwargs):
    if not indexnow_enabled() or not instance.pk:
        instance._indexnow_previous_state = None
        return

    try:
        previous = sender.objects.filter(pk=instance.pk).first()
        if not previous:
            instance._indexnow_previous_state = None
            return
        instance._indexnow_previous_state = {
            "slug": previous.slug,
            "indexable": _place_is_indexable(previous.pk),
            "snapshot": _significant_snapshot(previous),
        }
    except Exception:
        logger.exception("Could not capture previous IndexNow place state")
        instance._indexnow_previous_state = None


@receiver(post_save, sender=Place, dispatch_uid="indexnow_notify_place_save")
def notify_indexnow_after_place_save(sender, instance, created, **kwargs):
    if not indexnow_enabled():
        return

    try:
        previous_state = getattr(instance, "_indexnow_previous_state", None)
        previous_snapshot = (previous_state or {}).get("snapshot")
        update_fields = kwargs.get("update_fields")
        if created:
            significant_change = True
        elif update_fields is not None:
            significant_change = bool(set(update_fields) & SIGNIFICANT_PLACE_FIELDS)
        else:
            significant_change = previous_snapshot != _significant_snapshot(instance)
        previous_slug = (previous_state or {}).get("slug") or instance.slug
        previously_indexable = bool((previous_state or {}).get("indexable"))
    except Exception:
        logger.exception("Could not prepare IndexNow place notification")
        return

    transaction.on_commit(
        lambda: _safely_run(
            _notify_place_change,
            place_id=instance.pk,
            previous_slug=previous_slug,
            previously_indexable=previously_indexable,
            should_notify_current=significant_change,
        )
    )


def _notify_related_place_change(place_id: int) -> None:
    place = Place.objects.filter(pk=place_id).first()
    if not place or not _place_is_indexable(place_id):
        return
    enqueue_indexnow_urls(place_canonical_urls(place) + _indexable_seo_landing_urls())


@receiver(
    [post_save, post_delete],
    sender=PlacePhoto,
    dispatch_uid="indexnow_notify_place_photo_change",
)
@receiver(
    [post_save, post_delete],
    sender=PlaceScheduleDay,
    dispatch_uid="indexnow_notify_place_schedule_day_change",
)
def notify_indexnow_after_direct_place_relation_change(sender, instance, **kwargs):
    if indexnow_enabled() and instance.place_id:
        transaction.on_commit(
            lambda: _safely_run(_notify_related_place_change, instance.place_id)
        )


@receiver(
    [post_save, post_delete],
    sender=PlaceScheduleInterval,
    dispatch_uid="indexnow_notify_place_schedule_interval_change",
)
def notify_indexnow_after_schedule_interval_change(sender, instance, **kwargs):
    if indexnow_enabled() and instance.schedule_day_id:
        try:
            place_id = instance.schedule_day.place_id
        except Exception:
            logger.exception("Could not resolve IndexNow schedule place")
            return
        transaction.on_commit(
            lambda: _safely_run(_notify_related_place_change, place_id)
        )


@receiver(
    post_save,
    sender=CatalogContentSettings,
    dispatch_uid="indexnow_notify_seo_landing_change",
)
def notify_indexnow_after_catalog_content_save(sender, instance, **kwargs):
    if not indexnow_enabled():
        return
    transaction.on_commit(
        lambda: _safely_run(_notify_indexable_seo_landings)
    )
