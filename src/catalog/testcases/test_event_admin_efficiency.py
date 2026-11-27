"""Event entry boundaries: defaults, venue facts and contextual actions."""
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from catalog.domain_admin.place import EventAdmin
from catalog.models import Category, Event, Organization, Place
from catalog.testcases import admin as legacy_admin


class EventAdminEfficiencyTests(TestCase):
    def setUp(self):
        Category.objects.get_or_create(code='EDU', defaults={'name_az': 'Synthetic category'})
        self.actor = get_user_model().objects.create_superuser(
            'event-editor-qa', 'event-editor@example.invalid', 'synthetic')
        self.org = Organization.objects.create(owner=self.actor, name_az='Synthetic organizer')
        self.admin = EventAdmin(Event, AdminSite())
        self.request = RequestFactory().get('/admin/catalog/event/add/')
        self.request.user = self.actor

    def event(self, **changes):
        start = timezone.now() + timedelta(days=20)
        values = dict(name='Synthetic event', name_az='Synthetic event', category_id='EDU',
                      description_az='Synthetic description', organizer_organization=self.org,
                      event_format='online', status='draft', price_mode='unknown', start_datetime=start,
                      end_datetime=start + timedelta(hours=1), phone='+994501234567',
                      photo='events/synthetic.jpg', languages='az')
        values.update(changes)
        return Event.objects.create(**values)

    def test_portable_prompt_in_list_add_and_change(self):
        self.client.force_login(self.actor)
        event = self.event()
        for path in ('/admin/catalog/event/', '/admin/catalog/event/add/',
                     f'/admin/catalog/event/{event.pk}/change/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, 'id="event-editor-prompt"', count=1)
                self.assertContains(response, 'data-copy-event-prompt', count=1)
                self.assertContains(response, 'https://admin.kidsmap.az/admin/catalog/event/')
                self.assertContains(response, 'https://iticket.az/ru/page/rules')
                self.assertNotContains(response, '/home/ramin/')

    def test_editor_guide_is_available_on_each_surface_and_matches_the_copyable_prompt(self):
        from django.conf import settings
        from django.test.html import parse_html

        def elements(node):
            for child in node.children:
                if not isinstance(child, str):
                    yield child
                    yield from elements(child)

        self.client.force_login(self.actor)
        event = self.event()
        for language, heading in (('ru', 'Инструкция редактора афиши'),
                                  ('az', 'Afişa redaktoru üçün təlimat'),
                                  ('en', 'Event editor guide')):
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            for leaf in ('', 'add/', f'{event.pk}/change/'):
                with self.subTest(language=language, leaf=leaf):
                    response = self.client.get(f'/admin/catalog/event/{leaf}')
                    self.assertContains(response, 'id="event-editor-guide"', count=1)
                    self.assertContains(response, heading)
                    dom = parse_html(response.content.decode())
                    guide = next(el for el in elements(dom) if ('id', 'event-editor-guide') in el.attributes)
                    prompt = next(el for el in elements(dom) if ('id', 'event-editor-prompt') in el.attributes)
                    topics = [el for el in elements(guide) if el.name == 'li']
                    directory = next((el for el in elements(guide)
                                      if ('id', 'event-research-sources') in el.attributes), None)
                    self.assertIsNotNone(directory, 'Source directory missing from the staff guide')
                    groups = [
                        {dict(link.attributes)['href'] for link in elements(block) if link.name == 'a'}
                        for block in elements(directory) if block.name == 'dd'
                    ]
                    for related in (
                        {'https://iticket.az/', 'https://birbilet.az/az', 'https://biletli.az/', 'https://tickets.invitation.az/az'},
                        {'https://www.instagram.com/nationalartmuseum.az/', 'https://instagram.com/kukla_teatr'},
                        {'https://www.kuklateatri.az/az/repertory', 'https://nationalartmuseum.az/activities/events/'},
                        {'https://www.mcdonalds.az/news-notifications/24', 'https://www.mcdonalds.az/az/restaurant-locations'},
                        {'https://citycinema.az/en/afisha', 'https://linktr.ee/termit.baku'},
                        {'https://silkroadolympiad.org/project-olympiad/', 'https://azeristudent.az/events'},
                    ):
                        self.assertTrue(any(related <= urls for urls in groups))
                    coverage_heading = {
                        'ru': 'Как найти пробелы в афише',
                        'az': 'Afişada çatışmayan tədbirləri necə tapmaq olar',
                        'en': 'How to find gaps in the calendar',
                    }[language]
                    self.assertIn(coverage_heading, str(guide))
                    for url in set().union(*groups):
                        self.assertIn(url, prompt.children[0], 'Sources must travel with the copied task')
                    for term in ('Instagram', 'Reels', 'пресс-кит', 'фото спектакля', 'Условный пример'):
                        self.assertIn(term, prompt.children[0])
                    self.assertIn('Поиск по названию, афише или теме', prompt.children[0])
                    if language != 'ru':
                        self.assertNotIn('Поиск по названию, афише или теме', str(guide))
                    self.assertGreaterEqual(len(topics), 10)
                    self.assertIn('Детская афиша Баку', prompt.children[0])
                    self.assertIn('без слов', prompt.children[0])
                    self.assertIn('https://kidsmap.az/ru/afisha/', prompt.children[0])
                    self.assertNotIn('афишу или кадр', prompt.children[0])
                    if language == 'ru':
                        for topic in topics:
                            for block in elements(topic):
                                if block.name in ('strong', 'p'):
                                    self.assertIn(block.children[0], prompt.children[0])

    def test_view_only_staff_can_read_guide_without_copy_action(self):
        from django.contrib.auth.models import Permission

        staff = get_user_model().objects.create_user('event-reader', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_event'))
        self.client.force_login(staff)
        event = self.event()
        for path in ('/admin/catalog/event/', f'/admin/catalog/event/{event.pk}/change/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, 'id="event-editor-guide"', count=1)
                self.assertNotContains(response, 'data-copy-event-prompt')
                self.assertNotContains(response, 'name="_publish_event"')
                self.assertNotContains(response, 'data-event-repeat-form')

    def test_editor_can_select_and_reopen_multiple_event_languages(self):
        self.client.force_login(self.actor)
        event = self.event()
        change_url = f'/admin/catalog/event/{event.pk}/change/'
        for url in ('/admin/catalog/event/add/', change_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(b'name="languages"'), 4, url)
            self.assertContains(response, 'id="id_languages"', count=1)

        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(
            self, event, languages=['ru', 'az'], _continue='1')
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.languages, 'az,ru')
        reopened = self.client.get(change_url)
        field = reopened.context['adminform'].form['languages']
        self.assertEqual(field.value(), ['az', 'ru'])
        self.assertContains(reopened, str(field), html=True)

    def test_single_owned_organizer_is_initial_but_multiple_are_not_guessed(self):
        initial = self.admin.get_changeform_initial_data(self.request)
        self.assertEqual(initial.get('organizer_organization'), self.org.pk)
        Organization.objects.create(owner=self.actor, name_az='Second organizer')
        initial = self.admin.get_changeform_initial_data(self.request)
        self.assertNotIn('organizer_organization', initial)

    def test_related_venue_supplies_address_without_overwriting_event_phone(self):
        venue = Place.objects.create(name='Venue', name_az='Venue', category_id='EDU',
                                     address='Synthetic street 10', owner=self.actor,
                                     status='published', is_active=True, phone1='+994501111111',
                                     lat=40.409264, lng=49.867092)
        event = self.event(event_format='physical', related_place=venue, address='')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(address='', _publish_event='1')
        form = self.admin.get_form(self.request, event)(instance=event, data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['address'], 'Synthetic street 10')
        self.assertEqual(form.cleaned_data['phone'], '+994501234567')

    def test_return_action_requires_reason_and_preserves_pending_on_error(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': event.updated_at.isoformat(), 'reason': '', 'decision': 'return'})
        self.assertEqual(response.status_code, 400)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')

    def test_return_action_is_versioned_and_keeps_reason(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': event.updated_at.isoformat(),
            'reason': 'Please clarify the age', 'decision': 'return'})
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.status, 'rejected')
        self.assertEqual(event.rejection_reason, 'Please clarify the age')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': 'old-version', 'decision': 'approve'})
        self.assertEqual(response.status_code, 409)
        event.refresh_from_db()
        self.assertEqual(event.status, 'rejected')

    def test_review_and_repeat_actions_are_post_only(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        for action in ('review', 'repeat'):
            response = self.client.get(f'/admin/catalog/event/{event.pk}/{action}/')
            self.assertEqual(response.status_code, 405)

    def test_review_and_repeat_reject_missing_csrf_without_changing_source(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.actor)
        event = self.event(status='pending')
        count = Event.objects.count()
        for action in ('review', 'repeat'):
            response = client.post(f'/admin/catalog/event/{event.pk}/{action}/', {
                'expected_updated_at': event.updated_at.isoformat(), 'decision': 'approve'})
            self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')
        self.assertEqual(Event.objects.count(), count)

    def test_staff_without_event_permissions_cannot_review_or_repeat(self):
        staff = get_user_model().objects.create_user('event-no-permission', is_staff=True)
        self.client.force_login(staff)
        event = self.event(status='pending')
        for action in ('review', 'repeat'):
            response = self.client.post(f'/admin/catalog/event/{event.pk}/{action}/', {
                'expected_updated_at': event.updated_at.isoformat(), 'decision': 'approve'})
            self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')

    def test_published_description_cannot_be_cleared_by_ordinary_save(self):
        self.client.force_login(self.actor)
        event = self.event(status='published')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(description_az='', _continue='1')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.non_field_errors())
        event.refresh_from_db()
        self.assertEqual(event.description_az, 'Synthetic description')
        self.assertEqual(event.status, 'published')
