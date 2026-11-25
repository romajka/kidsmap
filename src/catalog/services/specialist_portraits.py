from django.db import transaction

from catalog.models import Specialist
from catalog.services.responsive_images import generate_variants


def public_portraits():
    return Specialist.objects.filter(
        status=Specialist.STATUS_PUBLISHED, is_active=True, photo__isnull=False,
    ).exclude(photo='').only('photo')


def prepare_published_portraits(ids, using):
    if not ids:
        return

    def prepare():
        # The final public photo may change again during moderation.
        for person in public_portraits().using(using).filter(pk__in=ids).iterator():
            generate_variants(person.photo, portrait=True)

    transaction.on_commit(prepare, using=using)
