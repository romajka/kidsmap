from django.db import models


class PlaceSpecialistMoveQuerySet(models.QuerySet):
    def public_targets(self):
        """Return retired places whose replacement profile is publicly accessible."""
        from catalog.models import Place, Specialist
        from catalog.services.content_quality import published_place_queryset
        from catalog.services.features import is_specialists_section_enabled

        if not is_specialists_section_enabled():
            return self.none()

        public_source = published_place_queryset(Place.objects.filter(pk=models.OuterRef('place_id')))
        return self.filter(
            ~models.Exists(public_source),
            specialist__status=Specialist.STATUS_PUBLISHED,
            specialist__is_active=True,
        )


class PlaceSpecialistMove(models.Model):
    """Keep old public place addresses and their localized metadata after a move."""

    place = models.OneToOneField('Place', on_delete=models.PROTECT, related_name='specialist_move')
    specialist = models.OneToOneField('Specialist', on_delete=models.PROTECT, related_name='place_move')
    localized_seo = models.JSONField(default=dict, blank=True)

    objects = PlaceSpecialistMoveQuerySet.as_manager()
