from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from catalog.models import AnalyticsActorExclusion, PlaceLike
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
