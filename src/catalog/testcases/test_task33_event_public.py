"""Published occurrences retain honest public detail and typed review parity."""
import json
from datetime import timedelta
from urllib.parse import urlsplit
from xml.etree import ElementTree
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
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

    def test_localized_event_links_share_one_clean_address(self):
        event = self.event(name_az='Xalçalar diyarı', start_datetime=self.now+timedelta(days=1),
                           end_datetime=self.now+timedelta(days=2))
        paths = {'az': '/event/xalcalar-diyari/', 'ru': '/ru/event/xalcalar-diyari/',
                 'en': '/en/event/xalcalar-diyari/'}
        for lang, path in paths.items():
            with self.subTest(lang=lang), override(lang):
                self.assertEqual(event.get_absolute_url(), path)
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(urlsplit(response.context['canonical_url']).path, path)
                self.assertEqual(urlsplit(json.loads(response.context['event_schema_json'])['url']).path, path)
                for code, alternate in paths.items():
                    self.assertContains(response, f'hreflang="{code}" href="http://testserver{alternate}"')
                self.assertContains(self.client.get(path.split('/event/')[0] + '/events/'), f'href="{path}"')
                old_prefix = path.removesuffix('xalcalar-diyari/') + f'{event.pk}-'
                for ending in ('xalcalar-diyari/', 'old-title/', 'old-title/?utm_source=shared'):
                    old = old_prefix + ending
                    self.assertRedirects(self.client.get(old), path, status_code=301, fetch_redirect_response=False)
                self.assertRedirects(self.client.get(path, {'utm_source': 'shared'}), path,
                                     status_code=301, fetch_redirect_response=False)
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
        event_paths = {urlsplit(node.text).path for node in sitemap.findall('.//{*}loc') if '/event/' in node.text}
        self.assertEqual(event_paths, set(paths.values()))

    def test_same_titles_and_digits_have_distinct_stable_destinations(self):
        one = self.event(name_az='2026 Yay²')
        two = self.event(name_az='2026 Yay²')
        for event in (one, two):
            self.assertRegex(event.get_absolute_url(), r'^/event/[a-z-]+/$')
        self.assertNotEqual(one.get_absolute_url(), two.get_absolute_url())
        old_path = two.get_absolute_url()
        two.name_az = 'Changed title'
        two.save(update_fields=['name_az'])
        self.assertEqual(two.get_absolute_url(), old_path)
        self.assertEqual(self.client.get(old_path).context['event'].pk, two.pk)
        self.assertRedirects(self.client.get(f'/event/{two.pk}-2026-yay-2/'), old_path,
                             status_code=301, fetch_redirect_response=False)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.filter(pk=two.pk).update(slug=one.slug)

    def test_legacy_paths_do_not_redirect_private_events(self):
        for event in (self.event(status='draft'), self.event(deleted_at=self.now)):
            with self.subTest(event=event.pk):
                self.assertEqual(self.client.get(f'/event/{event.pk}-old/').status_code, 404)
                self.assertEqual(self.client.get(event.get_absolute_url()).status_code, 404)

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

    def test_explicit_date_keeps_cancelled_card_with_state_instead_of_countdown(self):
        from django.urls import reverse
        event = self.event(occurrence_state='cancelled', start_datetime=self.now+timedelta(days=1), end_datetime=self.now+timedelta(days=2))
        with override('ru'):
            response = self.client.get(reverse('events_landing'), {'date':event.start_datetime.date().isoformat()})
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
