from django.conf import settings
from django.db import models


class PlaceLocationOverride(models.Model):
    """Historical exception, bound to exact coordinates and dataset version."""
    place = models.ForeignKey('catalog.Place', on_delete=models.CASCADE, related_name='location_overrides')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=1000)
    lat = models.FloatField()
    lng = models.FloatField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    automatic_city = models.CharField(max_length=100, blank=True)
    automatic_district = models.CharField(max_length=100, blank=True)
    automatic_status = models.CharField(max_length=32)
    dataset_version = models.CharField(max_length=64, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['place'], condition=models.Q(is_current=True), name='one_current_location_override')]
        ordering = ('-created_at',)
