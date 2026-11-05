"""Cabinet cards describe the same saved candidate as the authorized editor."""
from html.parser import HTMLParser

from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.translation import override

from catalog.models import OwnerTeamMembership, PlaceOwnershipRequest, SiteSettings, VolunteerPlaceRevision
from catalog.testcases.test_content_entry_final import CandidateMediaFixture


class CardMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.fill_links = []
        self.photo_counts = []
        self.photo_depth = 0
        self.metrics = {}
        self.metric = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'div' and attrs.get('data-owner-metric'):
            self.metric = attrs['data-owner-metric']
        if tag == 'a' and 'account-card-step-item__edit-link' in classes:
            self.fill_links.append(attrs['href'])
        if tag == 'span' and ('account-owner-card__photos' in classes or self.photo_depth):
            self.photo_depth += 1

    def handle_data(self, data):
        if self.photo_depth and data.strip().isdigit():
            self.photo_counts.append(int(data.strip()))
        if self.metric and data.strip().isdigit():
            self.metrics[self.metric] = int(data.strip())

    def handle_endtag(self, tag):
        if tag == 'span' and self.photo_depth:
            self.photo_depth -= 1
        if tag == 'div':
            self.metric = None


class OwnerDashboardCandidateTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.place.photo = self.stored('cabinet-main')
        self.place.save(update_fields=['photo'])
        SiteSettings.get_solo()
        self.client.force_login(self.owner)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'
        with override('ru'):
            self.url = reverse('owner_places_dashboard')

    def dashboard(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        row = next(p for p in response.context['managed_places'] if p.pk == self.place.pk)
        return response, row

    def test_submitted_candidate_shows_pending_without_duplicate_submit(self):
        self.propose({'description_az': 'Сохранённое описание для проверки.'}, submit=True)
        response, row = self.dashboard()
        self.assertContains(response, 'owner-status-badge-pending')
        self.assertEqual(response.context['pending_moderation_count'], 1)
        self.assertNotContains(response, 'action="'+reverse('owner_place_submit_review', args=[self.place.pk])+'"')
        self.assertIsNone(response.context['latest_editable_place'])

    def test_saved_candidate_readiness_and_title_match_editor_not_sparse_base(self):
        self.place.photo = ''
        self.place.description_az = ''
        self.place.save(update_fields=['photo', 'description_az'])
        self.propose({'name_ru': 'Сохранённая новая карточка', 'description_az': 'Описание сохранённой карточки.',
                      'photo': self.stored('candidate-only')})
        response, row = self.dashboard()
        self.assertEqual(row.completion['percent'], 100)
        self.assertContains(response, 'Сохранённая новая карточка')
        self.place.refresh_from_db()
        self.assertFalse(self.place.photo)
        self.assertEqual(self.place.description_az, '')

    def test_published_card_keeps_live_state_and_displays_pending_candidate(self):
        self.place.status = 'published'
        self.place.is_active = True
        self.place.save(update_fields=['status', 'is_active'])
        self.propose({'name_ru': 'Новое название на проверке'}, submit=True)
        response, row = self.dashboard()
        self.assertIn(row, response.context['published_places'])
        self.assertContains(response, 'account-status-pill--published')
        self.assertContains(response, 'owner-status-badge-pending')
        self.assertContains(response, 'Новое название на проверке')
        self.assertEqual(response.context['pending_moderation_count'], 1)

    def test_returned_and_declined_revision_notes_are_visible_and_pending_is_cleared(self):
        revision = self.propose({'description_az': 'Редактируемое описание.'})
        for status, label in [('rejected', 'Нужна доработка'), ('declined', 'Отклонено')]:
            with self.subTest(status=status):
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=status, review_note='Поясните вход со двора')
                response, row = self.dashboard()
                self.assertContains(response, label)
                self.assertContains(response, 'Поясните вход со двора')
                self.assertEqual(response.context['pending_moderation_count'], 0)

    def test_terminal_revision_does_not_reuse_candidate_readiness(self):
        revision = self.propose({'description_az': ''})
        for status, percent in [('draft', 92), ('pending', 92), ('rejected', 92), ('approved', 100), ('declined', 100)]:
            with self.subTest(status=status):
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=status)
                _, row = self.dashboard()
                self.assertEqual(row.completion['percent'], percent)

    def test_claim_request_does_not_override_returned_publication_state(self):
        revision = self.propose({'description_az': 'На доработке.'})
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='rejected', review_note='Уточните описание')
        PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner, request_kind='CLAIM')
        response, row = self.dashboard()
        self.assertContains(response, 'Нужна доработка')
        self.assertContains(response, 'Уточните описание')
        self.assertNotContains(response, 'owner-status-badge-pending')

    def test_observer_cannot_read_candidate_fields_or_notes(self):
        revision = self.propose({'name_az': 'Закрытый рабочий заголовок', 'description_az': ''})
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='rejected', review_note='Закрытое замечание')
        OwnerTeamMembership.objects.create(place=self.place, owner=self.owner, member=self.other, role='MODERATOR',
                                           base_ownership_version=self.place.ownership_version)
        self.client.force_login(self.other)
        response, row = self.dashboard()
        self.assertFalse(row.owner_can_edit)
        self.assertEqual(row.completion['percent'], 100)
        self.assertNotContains(response, 'Закрытый рабочий заголовок')
        self.assertNotContains(response, 'Закрытое замечание')

    def test_main_photo_is_counted_once(self):
        response, _ = self.dashboard()
        self.assertEqual(CardMarkup(response.content.decode()).photo_counts, [1])

    def test_saved_candidate_price_and_gallery_replace_base_presentation(self):
        self.propose({'photo': '', 'cover_photo': '', 'gallery': [
            {'id': None, 'image': self.stored('candidate-gallery'), 'caption': '', 'order': 0}],
            'pricing_plans': [{'product_type': 'lesson', 'price': 135, 'is_active': True}]})
        response, _ = self.dashboard()
        self.assertEqual(CardMarkup(response.content.decode()).photo_counts, [1])
        self.assertContains(response, '135')

    def test_empty_published_draft_is_not_presented_as_pending_changes(self):
        self.place.status = 'published'
        self.place.is_active = True
        self.place.save(update_fields=['status', 'is_active'])
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner, payload={}, status='draft')
        response, _ = self.dashboard()
        self.assertNotContains(response, 'data-owner-candidate')
        self.assertEqual(response.context['pending_moderation_count'], 0)

    def test_fill_links_target_sections_present_in_current_editor(self):
        self.place.age_from = None
        self.place.photo = ''
        self.place.lat = None
        self.place.lng = None
        self.place.save(update_fields=['age_from', 'photo', 'lat', 'lng'])
        response, _ = self.dashboard()
        links = CardMarkup(response.content.decode()).fill_links
        self.assertEqual({link.split('#')[-1] for link in links}, {'pc-section-2', 'pc-section-3', 'pc-section-4'})
        editor = self.client.get(reverse('owner_place_edit', args=[self.place.pk]))
        for link in links:
            self.assertContains(editor, 'id="'+link.split('#')[-1]+'"')

    def test_candidate_dashboard_get_does_not_write(self):
        self.propose({'name_az': 'Сохранённая версия без записи при чтении'})
        with CaptureQueriesContext(connection) as queries:
            self.dashboard()
        writes = [q['sql'] for q in queries if q['sql'].lstrip().upper().startswith(('UPDATE', 'INSERT', 'DELETE'))]
        self.assertEqual(writes, [])

    def test_published_pending_edits_count_as_review_but_not_unpublished(self):
        self.place.status = 'published'
        self.place.is_active = True
        self.place.save(update_fields=['status', 'is_active'])
        revision = self.propose({'description_az': 'Описание для повторной проверки.'}, submit=True)
        for status, review_count in [('pending', 1), ('rejected', 0)]:
            with self.subTest(status=status):
                VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=status)
                response, _ = self.dashboard()
                metrics = CardMarkup(response.content.decode()).metrics
                self.assertEqual(metrics, {'unpublished': 0, 'pending': review_count})
                self.assertContains(response, 'Не опубликовано')
                self.assertContains(response, 'На модерации')

    def test_newer_claim_does_not_hide_existing_publication_request_without_revision(self):
        PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner, request_kind='PUBLICATION')
        claim = PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner,
                                                     request_kind='CLAIM', status='REJECTED')
        response, row = self.dashboard()
        self.assertEqual(row.latest_moderation_request.pk, claim.pk)
        self.assertEqual(row.owner_workflow['status'], 'pending')
        self.assertEqual(response.context['pending_moderation_count'], 1)

    def test_multiple_groups_preserve_all_candidate_tariffs(self):
        groups = [{'id': None, 'name_az': f'Qrup {number}', 'age_from': 5, 'age_to': 8,
                   'language': 'az', 'schedule_text': 'Çərşənbə 15:00',
                   'pricing_plans': [{'product_type': 'lesson', 'price': str(100 + number * 7 + index)}
                                     for index in range(7)]} for number in range(2)]
        nested = {'pricing_schema_version': 2, 'activities': [{
            'id': None, 'name_az': 'Rəsm dərsi', 'description_az': 'Uşaqlar üçün rəsm məşğələsi.',
            'groups': groups}]}
        self.propose({'nested_pricing': nested, 'pricing_plans': []})
        _, row = self.dashboard()
        self.assertEqual(len(row.owner_saved_display._pricing_records_cache), 14)
        self.assertEqual({int(plan.price) for plan in row.owner_saved_display._pricing_records_cache},
                         set(range(100, 114)))
