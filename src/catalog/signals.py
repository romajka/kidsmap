from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_init, post_save
from django.dispatch import receiver

from catalog.models import AnalyticsActorExclusion, PlaceLike, Place, SiteGalleryImage
from catalog.services.favorite_metrics import reconcile_place_favorite_counts


def _reconcile_user_places(user_id):
    place_ids = list(PlaceLike.objects.filter(user_id=user_id).values_list("place_id", flat=True).distinct())
    if place_ids:
        reconcile_place_favorite_counts(place_ids=place_ids)


@receiver(post_save, sender=get_user_model())
def reconcile_after_user_state_change(sender, instance, **kwargs):
    _reconcile_user_places(instance.pk)


@receiver(post_save, sender=AnalyticsActorExclusion)
@receiver(post_delete, sender=AnalyticsActorExclusion)
def reconcile_after_exclusion_change(sender, instance, **kwargs):
    _reconcile_user_places(instance.user_id)


@receiver(post_save, sender=PlaceLike)
@receiver(post_delete, sender=PlaceLike)
def reconcile_after_favorite_change(sender, instance, **kwargs):
    reconcile_place_favorite_counts(place_ids=[instance.place_id])


@receiver(post_save, sender=Place)
@receiver(post_save, sender=SiteGalleryImage)
def prepare_responsive_photos(sender, instance, raw=False, **kwargs):
    if raw:
        return
    from catalog.services.responsive_images import generate_variants
    fields = ('photo', 'cover_photo') if sender is Place else ('image',)
    for field in fields:
        image = getattr(instance, field)
        if image:
            generate_variants(image)


@receiver(post_save, sender='catalog.Specialist')
@receiver(post_save, sender='catalog_moderation.ModerationSpecialist')
def prepare_specialist_portrait(sender, instance, raw, using, update_fields, **kwargs):
    if raw or (update_fields is not None and update_fields.isdisjoint({'photo', 'status', 'is_active'})):
        return
    if instance.status == instance.STATUS_PUBLISHED and instance.is_active and instance.photo:
        from catalog.services.specialist_portraits import prepare_published_portraits
        prepare_published_portraits([instance.pk], using)


@receiver(post_delete, sender='catalog.SpecialistProposalDocument')
def discard_proposal_document_file(sender, instance, using, **kwargs):
    from django.db import transaction
    if instance.file:
        storage, name = instance.file.storage, instance.file.name
        transaction.on_commit(lambda: storage.delete(name), using=using, robust=True)


@receiver(post_init, sender='catalog.Event')
@receiver(post_init, sender='catalog.EventPhoto')
def remember_event_image_source(sender, instance, **kwargs):
    from catalog.services.event_images import remember_source
    remember_source(instance)


@receiver(post_save, sender='catalog.Event')
@receiver(post_save, sender='catalog.EventPhoto')
def prepare_event_image_meta(sender, instance, raw=False, **kwargs):
    """Poster shape/colour and WebP sizes, once per uploaded file."""
    if raw:
        return
    from catalog.services.event_images import refresh_meta
    refresh_meta(instance)


@receiver(post_save)
@receiver(post_delete)
def invalidate_public_aggregates(sender, using, raw=False, **kwargs):
    from catalog.services.public_cache import affects_public_data, invalidate_on_commit
    if not raw and affects_public_data(sender):
        invalidate_on_commit(using)
