"""Published occurrences retain honest public detail and typed review parity."""
import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import override
from catalog.models import Category, Event, SiteSettings


class EventPublicContractTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='event-public', name_az='Event')
        self.now = timezone.now()

    def event(self, **kwargs):
        defaults = dict(name='Public event', name_ru='Public event', name_az='Public event',
            category=self.category, start_datetime=self.now-timedelta(days=2),
            end_datetime=self.now-timedelta(days=1), status='published', address='Historic address')
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    def response(self, event):
        with override('ru'):
            return self.client.get(event.get_absolute_url())

    def test_approved_past_detail_remains_public(self):
        response = self.response(self.event())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Завершено')

    def test_cancelled_and_rescheduled_detail_are_truthful(self):
        for state, label in [('cancelled','Отменено'), ('rescheduled','Перенесено')]:
            with self.subTest(state=state):
                event = self.event(occurrence_state=state, start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
                response = self.response(event)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, label)
                self.assertNotContains(response, 'data-temporary-event-timer')

    def test_cancelled_landing_card_has_state_instead_of_countdown(self):
        from django.urls import reverse
        self.event(occurrence_state='cancelled', start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
        with override('ru'):
            response = self.client.get(reverse('events_landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отменено')
        self.assertNotContains(response, 'data-temporary-event-timer')

    def test_unpublished_and_deleted_are_closed(self):
        for status in ['draft','pending','rejected']:
            self.assertEqual(self.response(self.event(status=status)).status_code, 404)
        self.assertEqual(self.response(self.event(deleted_at=self.now)).status_code, 404)

    def test_online_schema_has_no_physical_location(self):
        event = self.event(event_format='online', address='', start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
        response = self.response(event)
        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.context['event_schema_json'])
        self.assertEqual(schema['eventAttendanceMode'], 'https://schema.org/OnlineEventAttendanceMode')
        self.assertEqual(schema['location'], {'@type':'VirtualLocation'})
        self.assertNotIn('geo', schema['location'])
        self.assertNotIn('address', schema['location'])
        self.assertContains(response, 'Онлайн')

    def test_explicit_organizer_page_and_schema_match_without_venue_identity(self):
        from catalog.models import Organization, Specialist
        owner = get_user_model().objects.create_user(username='event-organizer')
        org = Organization.objects.create(name_az='Organizer AZ', name_ru='Organizer RU', status='published', approved_at=self.now, owner=owner)
        person = Specialist.objects.create(name='Independent organizer', status='published', is_active=True,
            verified_person_user=owner, person_verified_at=self.now)
        for fields, name, schema_type in [({'organizer_organization':org}, 'Organizer RU','Organization'),
                                          ({'organizer_specialist':person}, 'Independent organizer','Person')]:
            with self.subTest(schema_type=schema_type):
                event = self.event(**fields)
                response = self.response(event)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, name)
                schema = json.loads(response.context['event_schema_json'])
                self.assertEqual(schema['organizer']['name'], name)
                self.assertEqual(schema['organizer']['@type'], schema_type)

    def test_snapshot_and_jsonld_share_visible_facts_and_script_safety(self):
        event = self.event(name_ru='Event </script><img src=x>', start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
        Event.objects.filter(pk=event.pk).update(address='Changed address', venue_snapshot={'label':'Old venue','address':'Snapshot address','district':'baku_yasamal','lat':'40.4','lng':'49.8'})
        response = self.response(event)
        self.assertContains(response, 'Snapshot address')
        self.assertNotContains(response, 'Changed address')
        raw = response.context['event_schema_json']
        self.assertNotIn('</script>', raw)
        schema = json.loads(raw)
        self.assertEqual(schema['location']['address']['streetAddress'], 'Snapshot address')
        self.assertEqual(schema['location']['name'], 'Old venue')

    def test_pending_other_target_and_pending_edit_never_change_public_rating(self):
        from catalog.services.review_versions import submit_review, moderate_candidate
        event = self.event(start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
        other = self.event()
        author = get_user_model().objects.create_user(username='event-author')
        staff = get_user_model().objects.create_superuser(username='event-reviewer', email='event@example.test', password='fixture')
        head, revision = submit_review(target=event, user=author, rating=5, text='Approved event review')
        moderate_candidate(head=head, revision_id=revision.pk, actor=staff, approve=True)
        submit_review(target=event, user=author, rating=1, text='Pending edit')
        submit_review(target=other, user=author, rating=1, text='Other target pending')
        response = self.response(event)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved event review')
        self.assertNotContains(response, 'Pending edit')
        self.assertNotContains(response, 'Other target pending')
        self.assertEqual(response.context['event_rating'], {'average':5.0,'count':1})
        schema = json.loads(response.context['event_schema_json'])
        self.assertEqual(schema['aggregateRating']['ratingValue'], 5.0)
        self.assertEqual(schema['aggregateRating']['reviewCount'], 1)
        self.assertEqual(len(schema['review']), 1)
