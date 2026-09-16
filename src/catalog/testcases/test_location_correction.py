from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from catalog.models import Category, Place, PlaceChangeAudit


class LocationCorrectionTests(TestCase):
    def setUp(self):
        category, _ = Category.objects.get_or_create(code='EDU', defaults={'name': 'Education'})
        self.place = Place.objects.create(name='Museum correction fixture', category=category,
            lat=40.360, lng=49.835, status='draft', is_active=False)
        Place.objects.filter(pk=self.place.pk).update(district='baku_yasamal', city='', location_resolution_status='legacy')
        self.actor = get_user_model().objects.create_superuser('correction-admin', 'admin@example.invalid', 'pass')
        self.options = dict(place_id=self.place.pk, expected_district='baku_yasamal',
                            expected_lat=40.360, expected_lng=49.835, expected_city='')

    def test_preview_never_writes_and_apply_is_audited_and_idempotent(self):
        call_command('correct_place_location', **self.options, stdout=StringIO())
        self.place.refresh_from_db()
        self.assertEqual(self.place.district, 'baku_yasamal')
        self.assertEqual(PlaceChangeAudit.objects.filter(place=self.place).count(), 0)
        call_command('correct_place_location', **self.options, apply=True, actor_id=self.actor.pk, stdout=StringIO())
        self.place.refresh_from_db()
        self.assertEqual((self.place.city, self.place.district), ('baku', 'baku_sabail'))
        count = PlaceChangeAudit.objects.filter(place=self.place).count()
        self.assertGreater(count, 0)
        call_command('correct_place_location', **self.options, apply=True, actor_id=self.actor.pk, stdout=StringIO())
        self.assertEqual(PlaceChangeAudit.objects.filter(place=self.place).count(), count)

    def test_coordinate_conflict_and_unprivileged_actor_cannot_apply(self):
        with self.assertRaises(CommandError):
            call_command('correct_place_location', **{**self.options, 'expected_lat': 40.4}, apply=True, actor_id=self.actor.pk)
        user = get_user_model().objects.create_user('correction-user')
        with self.assertRaises(CommandError):
            call_command('correct_place_location', **self.options, apply=True, actor_id=user.pk)
        self.place.refresh_from_db()
        self.assertEqual(self.place.district, 'baku_yasamal')
