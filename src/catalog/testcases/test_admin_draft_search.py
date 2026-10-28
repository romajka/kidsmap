"""Admin search must find saved content without exposing private revisions."""
import json

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.models import Category, Place, ServerDraft, VolunteerPlaceRevision
from catalog.services.place_editor_drafts import working_draft_rows


class AdminSavedDraftSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            'draft-search-staff', 'draft-search@example.invalid', 'fictional')
        cls.viewer = get_user_model().objects.create_user('draft-search-viewer', is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename='view_place'))
        cls.category = Category.objects.create(code='QA_SEARCH', name_az='Search fixture')
        cls.place = Place(name='Stored Search Club', name_az='Stored Search Club', slug='stored-search-club',
                          category=cls.category, address='', phone1='', status='draft', is_active=False)
        Place.objects.bulk_create([cls.place])
        cls.revision = VolunteerPlaceRevision.objects.create(place=cls.place, author=cls.staff,
            status='draft', payload={'name_ru': 'Сохранённый клуб', 'name_en': 'Saved Search Club',
                'address': 'Candidate Avenue 987', 'phone1': '+994501234987',
                'phone2': '+994551234987', 'phone3': '+994701234987',
                'instagram': 'candidate_search_club', 'moderation_note': 'PrivateReviewMarker'})

    def search(self, term, *, user=None, queryset=None):
        request = RequestFactory().get('/admin/catalog/place/', {'q': term})
        request.user = user or self.staff
        request.LANGUAGE_CODE = 'ru'
        model_admin = admin.site._registry[Place]
        queryset = model_admin.get_queryset(request) if queryset is None else queryset
        results, _ = model_admin.get_search_results(request, queryset, term)
        return list(results.values_list('pk', flat=True))

    def test_search_finds_candidate_only_fields(self):
        for term in ('Сохранённый', 'Saved Search Club', 'Candidate Avenue 987',
                     '+994501234987', '+994551234987', '+994701234987', 'candidate_search_club'):
            with self.subTest(term=term):
                self.assertEqual(self.search(term), [self.place.pk])

    def test_terms_can_match_saved_address_and_unchanged_name(self):
        self.assertEqual(self.search('Stored Avenue'), [self.place.pk])

    def test_quoted_terms_preserve_phrase_search(self):
        self.assertEqual(self.search('Stored "Candidate Avenue"'), [self.place.pk])
        self.assertEqual(self.search('"Avenue Candidate"'), [])

    def test_only_active_revision_statuses_participate(self):
        for status, found in (('draft', True), ('pending', True), ('rejected', True),
                              ('approved', False), ('declined', False)):
            with self.subTest(status=status):
                VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status=status)
                self.assertEqual(self.search('Candidate Avenue'), [self.place.pk] if found else [])

    def test_candidate_search_preserves_incoming_filters(self):
        self.assertEqual(self.search('Candidate Avenue', queryset=Place.objects.none()), [])
        self.assertEqual(self.search('Candidate Avenue',
            queryset=Place.objects.filter(is_active=True)), [])

    def test_view_permission_does_not_reveal_saved_revision_fields(self):
        self.assertEqual(self.search('Stored Search', user=self.viewer), [self.place.pk])
        self.assertEqual(self.search('Candidate Avenue', user=self.viewer), [])
        self.assertEqual(self.search('+994501234987', user=self.viewer), [])

    def test_revoked_actor_cannot_search_or_receive_candidate_details(self):
        get_user_model().objects.filter(pk=self.staff.pk).update(is_active=False)
        self.assertEqual(self.search('Candidate Avenue'), [])
        rows = self.suggestions('Stored Search')
        self.assertEqual((rows[0]['address'], rows[0]['phone']), ('', ''))

    def test_search_does_not_scan_arbitrary_revision_metadata(self):
        self.assertEqual(self.search('PrivateReviewMarker'), [])

    def test_saved_search_does_not_change_live_fields_or_revision(self):
        self.assertEqual(self.search('Candidate Avenue'), [self.place.pk])
        place = Place.objects.get(pk=self.place.pk)
        self.assertEqual((place.address, place.phone1, place.status, place.is_active),
                         ('', '', 'draft', False))
        self.assertEqual(VolunteerPlaceRevision.objects.get(pk=self.revision.pk).version, 1)

    def test_own_working_copy_match_keeps_its_target_in_search_results(self):
        ServerDraft.objects.create(actor=self.staff, target_type='place', target_id=self.place.pk,
            source_version=self.place.content_version,
            fields={'name_az': 'Own private target', 'address': 'Own Working Avenue 321'})
        self.assertEqual(self.search('Own Working Avenue'), [self.place.pk])
        self.assertEqual(self.search('Own Working Avenue', queryset=Place.objects.none()), [])

    def test_another_actors_working_copy_is_not_searchable_even_by_superuser(self):
        ServerDraft.objects.create(actor=self.viewer, target_type='place', target_id=self.place.pk,
            source_version=self.place.content_version,
            fields={'address': 'Other Working Avenue 654'})
        self.assertEqual(self.search('Other Working Avenue'), [])

    def test_explicitly_cleared_candidate_field_is_not_replaced_by_live_value(self):
        Place.objects.filter(pk=self.place.pk).update(address='Obsolete Address')
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(
            payload={'address': '', 'phone1': '+994501234987'})
        self.assertEqual(self.search('Obsolete +994501234987'), [])

    def test_changelist_search_returns_saved_address_match(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:catalog_place_changelist'), {'q': 'Candidate Avenue'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['cl'].result_list.values_list('pk', flat=True)),
                         [self.place.pk])

    def suggestions(self, term, *, user=None):
        request = RequestFactory().get('/admin/catalog/place/search-suggestions/', {'q': term})
        request.user = user or self.staff
        request.LANGUAGE_CODE = 'en'
        return json.loads(admin.site._registry[Place].search_suggestions_view(request).content)['results']

    def test_search_suggestions_find_and_display_saved_candidate_values(self):
        rows = self.suggestions('Candidate Avenue')
        self.assertEqual([row['id'] for row in rows], [self.place.pk])
        self.assertEqual((rows[0]['label'], rows[0]['address'], rows[0]['phone']),
                         ('Saved Search Club', 'Candidate Avenue 987', '+994501234987'))

    def test_search_suggestions_do_not_disclose_candidate_values_to_viewer(self):
        self.assertEqual(self.suggestions('Candidate Avenue', user=self.viewer), [])
        rows = self.suggestions('Stored Search', user=self.viewer)
        self.assertEqual((rows[0]['label'], rows[0]['address'], rows[0]['phone']),
                         ('Stored Search Club', '', ''))


class PrivateWorkingDraftSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            'private-search-staff', 'private-search@example.invalid', 'fictional')
        cls.other = get_user_model().objects.create_superuser(
            'private-search-other', 'private-other@example.invalid', 'fictional')
        cls.draft = ServerDraft.objects.create(actor=cls.staff, target_type='place', fields={
            'name_az': 'Özəl klub', 'name_ru': 'Рабочий клуб', 'name_en': 'Private Search Club',
            'address': 'Private Avenue 654', 'phone1': '+994501234654',
            'website': 'https://private-search.example.invalid',
            'moderation_note': 'PrivateInternalMarker'})
        ServerDraft.objects.create(actor=cls.other, target_type='place',
            fields={'name_az': 'Other club', 'address': 'Other Avenue 321'})

    def rows(self, term):
        return list(working_draft_rows(user=self.staff, query=term))

    def test_finds_own_draft_by_address_contact_and_other_language(self):
        for term in ('Private Avenue', '+994501234654', 'private-search.example.invalid',
                     'Рабочий', 'Private Search Club'):
            with self.subTest(term=term):
                self.assertEqual([row['id'] for row in self.rows(term)], [str(self.draft.pk)])

    def test_private_draft_search_keeps_actor_scope_and_metadata_private(self):
        self.assertEqual(self.rows('Other Avenue'), [])
        self.assertEqual(self.rows('PrivateInternalMarker'), [])

    def test_private_draft_search_matches_words_across_fields(self):
        self.assertEqual([row['id'] for row in self.rows('"Private Avenue" клуб')],
                         [str(self.draft.pk)])
