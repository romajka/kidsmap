"""General approximate ages remain searchable without individual performances."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.models import Place
from catalog.services.filtering import PlaceListFilters
from catalog.services.map_payload import serialize_map_places
from catalog.testcases.utils import create_quality_place, create_ready_place


class PlaceProgrammeAgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from catalog.testcases.utils import ensure_quality_subcategory
        ensure_quality_subcategory('EDU')

    def mark_variable(self, place):
        self.assertTrue(hasattr(place, 'age_varies_by_program'), 'Place must persist programme-dependent ages')
        place.age_varies_by_program = True
        place.save(update_fields=['age_varies_by_program'])
        return place

    def test_owner_admin_and_volunteer_editors_offer_the_same_optional_checkbox(self):
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.volunteer_forms import VolunteerPlaceForm
        for form in (OwnerPlaceCreateForm(), OwnerPlaceEditForm(), PlaceAdminForm(), VolunteerPlaceForm()):
            with self.subTest(form=type(form).__name__):
                self.assertIn('age_varies_by_program', form.fields)
                self.assertFalse(form.fields['age_varies_by_program'].required)
                self.assertTrue(form.fields['age_varies_by_program'].help_text)
                self.assertEqual(form.fields['age_varies_by_program'].widget.input_type, 'checkbox')

    def test_legacy_cards_default_to_exact_and_keep_their_label(self):
        place = create_quality_place(age_from=3, age_to=12)
        self.assertTrue(hasattr(place, 'age_varies_by_program'))
        self.assertFalse(place.age_varies_by_program)
        self.assertEqual(place.age_public_label, '3–12')
        self.assertEqual(place.age_program_note, '')

    def test_localized_approximate_label_and_note(self):
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12))
        for lang, expected, note in (
            ('ru', 'Ориентировочно 3–12', 'зависит от программы'),
            ('az', 'Təxminən 3–12', 'məhdudiyyətləri dəqiqləşdirin'),
            ('en', 'Approximately 3–12', 'depends on the programme'),
        ):
            with self.subTest(lang=lang), override(lang):
                self.assertEqual(place.age_public_label, expected)
                self.assertIn(note, place.age_program_note)

    def test_age_range_filters_work_without_performance_or_group_rows(self):
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12, district='baku_sabail'))
        for params, found in (({'age':'3'}, True), ({'age':'5'}, True), ({'age':'12'}, True),
                              ({'age':'14'}, False), ({'age':'0'}, False),
                              ({'age_from':'6','age_to':'9'}, True),
                              ({'age':'5','district':'sumgait'}, False),
                              ({'age':'5','category':'SPORT'}, False)):
            with self.subTest(params=params):
                self.assertEqual(PlaceListFilters(**params).apply(Place.objects.filter(pk=place.pk)).exists(), found)

    def test_checkbox_does_not_make_missing_ages_match_every_age(self):
        place = self.mark_variable(create_quality_place(age_from=None, age_to=None))
        self.assertFalse(PlaceListFilters(age='5').apply(Place.objects.filter(pk=place.pk)).exists())
        self.assertEqual(place.age_public_label, '')

    def test_flag_does_not_bypass_range_validation_or_readiness(self):
        from catalog.services.place_readiness import evaluate_place_readiness
        place = self.mark_variable(create_ready_place(age_from=3, age_to=12))
        self.assertTrue(evaluate_place_readiness(place).is_ready)
        place.age_from = 12
        place.age_to = 3
        with self.assertRaises(ValidationError):
            place.clean()
        place.age_from = place.age_to = None
        self.assertIn('age', [issue.code for issue in evaluate_place_readiness(place).issues])

    def test_filtered_card_and_map_keep_the_approximate_range(self):
        from django.template.loader import render_to_string
        from catalog.services.public_presentation import prepare_cards
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12))
        filters = PlaceListFilters(age='5')
        qs = Place.objects.filter(pk=place.pk)
        with override('ru'):
            card = prepare_cards(filters.apply(qs), 'ru', filters=filters)[0]
            html = render_to_string('catalog/includes/place_card.html', {'place':card, 'presentation':card._card_presentation, 'card_language':'ru'})
            self.assertIn('Ориентировочно 3–12', html)
            self.assertIn('зависит от программы', html)
            points = serialize_map_places(qs, 'ru', filters=filters)
            self.assertEqual(points[0]['members'][0]['age'], 'Ориентировочно 3–12 лет')
            self.assertIn('зависит от программы', points[0]['members'][0]['age_note'])
        self.assertEqual(serialize_map_places(qs, 'ru', filters=PlaceListFilters(age='14')), [])

    def test_drafts_stay_off_the_public_map(self):
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12, status=Place.STATUS_DRAFT))
        self.assertEqual(serialize_map_places(Place.objects.filter(pk=place.pk), 'ru', filters=PlaceListFilters(age='5')), [])

    def test_admin_export_and_candidate_snapshot_keep_the_flag(self):
        from catalog.services.volunteer_places import content_snapshot, candidate_from_payload
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12))
        snapshot = content_snapshot(place)
        self.assertIs(snapshot.get('age_varies_by_program'), True)
        self.assertFalse(candidate_from_payload(place, {**snapshot, 'age_varies_by_program':False}).age_varies_by_program)
        staff = get_user_model().objects.create_superuser('age-export', 'age@example.invalid', 'synthetic-only')
        self.client.force_login(staff)
        data = self.client.get(reverse('admin:catalog_place_export_json', args=[place.pk])).json()
        self.assertIs(data.get('age_varies_by_program'), True)

    def test_owner_form_retains_checked_and_unchecked_values(self):
        place = create_ready_place()
        for checked in (True, False):
            form = OwnerPlaceEditForm(instance=place)
            self.assertIn('age_varies_by_program', form.fields)
            data = model_to_dict(place, fields=form.Meta.fields)
            data.update(region='baku', district='', offers_adult_classes='0', form_action='save_draft',
                        age_varies_by_program='on' if checked else '', photo='')
            form = OwnerPlaceEditForm(data=data, instance=place)
            self.assertTrue(form.is_valid(), form.errors.as_json())
            saved = form.save(commit=False)
            self.assertIs(saved.age_varies_by_program, checked)
            saved.save()
            saved.refresh_from_db()
            self.assertIs(saved.age_varies_by_program, checked)
            place = saved

    def test_unbatched_cards_keep_age_labels_in_the_requested_language(self):
        from catalog.services.public_presentation import present
        place = self.mark_variable(create_quality_place(age_from=3, age_to=12))
        with override('ru'):
            self.assertEqual(present(place, 'en').get('age_label'), 'Approximately 3–12')
        place.age_varies_by_program = False
        self.assertEqual(present(place, 'ru').get('age_label'), '3–12')

    def test_private_server_draft_retains_checkbox_without_changing_live(self):
        import json
        owner = get_user_model().objects.create_user('age-draft-owner')
        place = create_quality_place(owner=owner, created_by=owner, age_from=3, age_to=12)
        self.client.force_login(owner)
        data = {'target_type':'place', 'target_id':place.pk, 'schema_version':1,
                'expected_version':0, 'source_version':place.content_version, 'fields':{'age_varies_by_program':True}}
        response = self.client.post(reverse('server_draft_collection'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        saved = response.json()
        resumed = self.client.get(reverse('server_draft_detail', args=[saved['draft_id']]))
        self.assertIs(resumed.json()['fields']['age_varies_by_program'], True)
        place.refresh_from_db()
        self.assertFalse(place.age_varies_by_program)
        data.update(draft_id=saved['draft_id'], expected_version=saved['version'], fields={'age_varies_by_program':False})
        response = self.client.post(reverse('server_draft_collection'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIs(response.json()['fields']['age_varies_by_program'], False)

    def test_old_revision_without_new_false_field_keeps_its_base_but_detects_real_change(self):
        from types import SimpleNamespace
        from catalog.services.volunteer_places import live_snapshot, revision_base_matches
        place = create_quality_place()
        base = live_snapshot(place)
        base.pop('age_varies_by_program', None)
        revision = SimpleNamespace(dependencies={}, base_snapshot=base)
        self.assertTrue(revision_base_matches(revision, place))
        place.age_varies_by_program = True
        self.assertFalse(revision_base_matches(revision, place))

    def test_owner_proposal_publishes_the_flag_only_after_moderator_approval(self):
        from catalog.services import publication
        owner = get_user_model().objects.create_user('age-proposal-owner')
        staff = get_user_model().objects.create_superuser('age-reviewer', 'reviewer@example.invalid', 'synthetic-only')
        place = create_ready_place(owner=owner, created_by=owner, age_from=3, age_to=12)
        revision = publication.propose(actor=owner, target_type='place', target_id=place.pk,
            patch={'age_varies_by_program':True}, schema_version=1,
            expected_version=place.content_version, revision_version=0, submit=True, explicit_save=True)
        place.refresh_from_db()
        self.assertFalse(place.age_varies_by_program)
        publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
        place.refresh_from_db()
        self.assertTrue(place.age_varies_by_program)
