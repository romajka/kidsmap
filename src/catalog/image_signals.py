from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save

from catalog.models import (
    Event,
    EventPhoto,
    Place,
    PlacePhoto,
    SiteAboutSettings,
    SiteBrandingSettings,
    SiteEmptyStateSettings,
    SiteGalleryImage,
    SiteSettings,
    Specialist,
    UserProfile,
)
from catalog.services.images import delete_image_and_variants, generate_image_variants


SITE_SETTINGS_IMAGE_PROFILES = {
    "site_background_image": "background",
    "home_hero_image": "hero",
    "catalog_hero_image": "hero",
    "about_hero_image": "hero",
    "reviews_hero_image": "hero",
    "for_business_hero_image": "hero",
    "dashboard_hero_image": "hero",
    "empty_results_image": "illustration",
}


MODEL_IMAGE_PROFILES = {
    Place: {"photo": "listing", "cover_photo": "listing"},
    PlacePhoto: {"image": "listing"},
    Event: {"photo": "listing"},
    EventPhoto: {"image": "listing"},
    Specialist: {"photo": "profile"},
    UserProfile: {"avatar": "profile"},
    SiteGalleryImage: {"image": "hero_gallery"},
    SiteSettings: SITE_SETTINGS_IMAGE_PROFILES,
    SiteBrandingSettings: SITE_SETTINGS_IMAGE_PROFILES,
    SiteAboutSettings: SITE_SETTINGS_IMAGE_PROFILES,
    SiteEmptyStateSettings: SITE_SETTINGS_IMAGE_PROFILES,
}


def _remember_replaced_images(sender, instance, **kwargs):
    if not instance.pk:
        instance._replaced_image_files = []
        instance._changed_image_fields = list(MODEL_IMAGE_PROFILES[sender])
        return

    try:
        previous = sender._base_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._replaced_image_files = []
        instance._changed_image_fields = list(MODEL_IMAGE_PROFILES[sender])
        return

    replaced = []
    changed = []
    for field_name, profile in MODEL_IMAGE_PROFILES[sender].items():
        old_file = getattr(previous, field_name, None)
        new_file = getattr(instance, field_name, None)
        old_name = getattr(old_file, "name", "") or ""
        new_name = getattr(new_file, "name", "") or ""
        is_new_upload = bool(new_file and not getattr(new_file, "_committed", True))
        if old_name != new_name or is_new_upload:
            changed.append(field_name)
            if old_name:
                replaced.append((old_file, profile))
    instance._replaced_image_files = replaced
    instance._changed_image_fields = changed


def _process_saved_images(sender, instance, created, **kwargs):
    profiles = MODEL_IMAGE_PROFILES[sender]
    changed = list(profiles) if created else getattr(instance, "_changed_image_fields", [])
    files_to_generate = [
        (getattr(instance, field_name, None), profiles[field_name])
        for field_name in changed
        if getattr(instance, field_name, None)
    ]
    files_to_delete = getattr(instance, "_replaced_image_files", [])

    def process():
        for file_field, profile in files_to_generate:
            generate_image_variants(file_field, profile)
        for file_field, profile in files_to_delete:
            delete_image_and_variants(file_field, profile)

    transaction.on_commit(process)


def _delete_model_images(sender, instance, **kwargs):
    files = [
        (getattr(instance, field_name, None), profile)
        for field_name, profile in MODEL_IMAGE_PROFILES[sender].items()
        if getattr(instance, field_name, None)
    ]
    transaction.on_commit(lambda: [delete_image_and_variants(file_field, profile) for file_field, profile in files])


def register_image_signals() -> None:
    for model in MODEL_IMAGE_PROFILES:
        label = model._meta.label_lower
        pre_save.connect(
            _remember_replaced_images,
            sender=model,
            weak=False,
            dispatch_uid=f"catalog.images.pre_save.{label}",
        )
        post_save.connect(
            _process_saved_images,
            sender=model,
            weak=False,
            dispatch_uid=f"catalog.images.post_save.{label}",
        )
        post_delete.connect(
            _delete_model_images,
            sender=model,
            weak=False,
            dispatch_uid=f"catalog.images.post_delete.{label}",
        )
