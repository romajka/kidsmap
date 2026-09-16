"""Preview by default; apply one explicitly identified coordinate-based correction."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Place, PlaceChangeAudit
from catalog.services.district_geometry import resolve_location
from catalog.services.staff_roles import is_volunteer


class Command(BaseCommand):
    help = 'Preview or apply one location correction, guarded by expected current values.'

    def add_arguments(self, parser):
        parser.add_argument('--place-id', type=int, required=True)
        parser.add_argument('--expected-district', required=True)
        parser.add_argument('--expected-city', required=True)
        parser.add_argument('--expected-lat', type=float, required=True)
        parser.add_argument('--expected-lng', type=float, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--actor-id', type=int)

    def handle(self, *args, **options):
        # Preview does not acquire a write lock or persist metadata.
        if not options['apply']:
            place = Place.objects.filter(pk=options['place_id']).first()
            if not place:
                raise CommandError('Place not found.')
            self.correct(place, options, apply=False)
            return
        actor = get_user_model().objects.filter(pk=options['actor_id']).first()
        if not actor or not actor.is_active or not actor.is_staff or is_volunteer(actor) or not actor.has_perm('catalog.change_place'):
            raise CommandError('Apply requires an active staff actor with change_place permission.')
        with transaction.atomic():
            place = Place.objects.select_for_update().filter(pk=options['place_id']).first()
            if not place:
                raise CommandError('Place not found.')
            self.correct(place, options, apply=True, actor=actor)

    def correct(self, place, options, *, apply, actor=None):
        if (place.lat, place.lng) != (options['expected_lat'], options['expected_lng']):
            raise CommandError('Coordinates changed; inspect the record again.')
        result = resolve_location(place.lat, place.lng)
        if result.status != 'resolved':
            raise CommandError('Point does not resolve unambiguously; manual review required.')
        if place.location_resolution_status == 'overridden':
            raise CommandError('Active administrative exception; review it before correction.')
        if (place.city, place.district, place.location_dataset_version) == (result.city_key, result.district_key, result.dataset_version):
            self.stdout.write('Already correct; no changes.')
            return
        if (place.city, place.district) != (options['expected_city'], options['expected_district']):
            raise CommandError('Administrative values changed; inspect the record again.')
        self.stdout.write(f'Place {place.pk}: {place.city}/{place.district} -> {result.city_key}/{result.district_key}; dataset={result.dataset_version}')
        if not apply:
            self.stdout.write('Preview only; no changes.')
            return
        before = {'city': place.city, 'district': place.district}
        place.city, place.district = result.city_key, result.district_key
        place.save(update_fields=['city', 'district', 'updated_at'])
        for field, old_value in before.items():
            if old_value != getattr(place, field):
                PlaceChangeAudit.objects.create(place=place, changed_by=actor, source=PlaceChangeAudit.SOURCE_ADMIN,
                    field_name=field, old_value=old_value, new_value=getattr(place, field))
        self.stdout.write('Applied and audited.')
