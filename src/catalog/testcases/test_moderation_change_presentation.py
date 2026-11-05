"""Reviewers can locate changes without altering the candidate or leaking HTML."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import VolunteerPlaceRevision
from catalog.services import publication, moderation_hub
from catalog.testcases.utils import create_quality_place


class ModerationChangePresentationTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser('change_reviewer', 'qa@example.invalid', 'synthetic')
        self.place = create_quality_place(owner=self.staff, created_by=self.staff, with_subcategory=True)
        self.place.status = 'published'
        self.place.description_ru = 'Занятия проходят по будням утром.'
        self.place.save()
        self.revision = publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'description_ru': 'Занятия проходят по выходным утром.'}, schema_version=1,
            expected_version=self.place.content_version)
        self.client.force_login(self.staff)
        self.url = reverse('admin:volunteer_moderation_detail', args=['content', self.revision.pk])

    def test_index_names_fields_and_detail_links_to_exact_changes(self):
        with override('ru'):
            rows, _ = moderation_hub.query(self.staff, {})
            self.assertEqual(rows[0]['change_labels'], ['Описание (RU)'])
            response = self.client.get('/ru' + self.url)
        self.assertContains(response, 'href="#moderation-change-1"')
        self.assertContains(response, 'id="moderation-change-1"')
        self.assertContains(response, '<del>будням</del>', html=False)
        self.assertContains(response, '<ins>выходным</ins>', html=False)
        self.revision.refresh_from_db()
        self.assertEqual((self.revision.status, self.revision.version), ('pending', 1))

    def test_markup_from_proposal_is_escaped(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'description_ru': '<script>alert(1)</script>'})
        response = self.client.get('/ru' + self.url)
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_removed_value_and_zero_are_not_empty_equivalents(self):
        from catalog.services.moderation_changes import describe_change
        with override('ru'):
            removed = describe_change('phone', '123', '')
            zero = describe_change('price', 1, 0)
            false = describe_change('is_active', True, False)
        self.assertEqual(removed['change_type'], 'removed')
        self.assertEqual(zero['change_type'], 'changed')
        self.assertEqual(zero['after_text'], '0')
        self.assertEqual(false['after_text'], 'Нет')

    def test_conflict_compares_current_not_old_base(self):
        type(self.place).objects.filter(pk=self.place.pk).update(description_ru='Другая текущая версия')
        row = moderation_hub.detail(self.staff, 'content', self.revision.pk)
        self.assertTrue(row['conflict'])
        self.assertEqual(row['display_changes'][0]['before_text'], 'Другая текущая версия')

    def test_editor_has_pending_review_banner(self):
        response = self.client.get('/ru' + reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertContains(response, 'data-pending-change-review')
        self.assertContains(response, self.url)

    def test_nonstaff_cannot_read_change_details(self):
        self.staff.is_staff = False; self.staff.is_superuser = False; self.staff.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_new_entry_without_patch_still_displays_information_to_review(self):
        from catalog.models import Organization
        org = Organization.objects.create(name_az='New synthetic organization', owner=self.staff, created_by=self.staff)
        revision = publication.propose(actor=self.staff, target_type='organization', target_id=org.pk,
            patch={}, schema_version=1, expected_version=org.content_version)
        row = moderation_hub.detail(self.staff, 'content', revision.pk)
        self.assertTrue(any(c['after_text'] == org.name_az for c in row['display_changes']))

    def test_empty_edit_has_explicit_empty_state_and_no_fake_changes(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={}, changed_fields=[])
        response = self.client.get('/ru' + self.url)
        self.assertContains(response, 'В предложении нет изменённых полей.')
        self.assertNotContains(response, 'class="km-change-field"')

    def test_completed_candidate_does_not_show_pending_banner(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status='approved')
        response = self.client.get('/ru' + reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertNotContains(response, 'data-pending-change-review')

    def test_large_diff_preserves_every_character_with_bounded_fragments(self):
        from catalog.services.moderation_changes import describe_change
        before, after = ('a b ' * 6000), ('a c ' * 6000)
        result = describe_change('description_ru', before, after)
        self.assertEqual(''.join(p['text'] for p in result['before_parts']), before)
        self.assertEqual(''.join(p['text'] for p in result['after_parts']), after)
        self.assertEqual(len(result['after_parts']), 1)

    def test_new_review_copy_is_localized(self):
        for lang, title in [('ru', 'Что изменено'), ('az', 'Nə dəyişib'), ('en', 'What changed')]:
            with override(lang):
                row = moderation_hub.detail(self.staff, 'content', self.revision.pk)
            self.assertEqual(row['review_copy']['title'], title)

    def test_draft_is_not_described_as_a_completed_decision(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status='draft')
        response = self.client.get('/ru' + self.url)
        self.assertNotContains(response, 'Решение по этой заявке уже принято.')

    def test_completed_conflict_does_not_ask_to_return_an_archived_proposal(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status='approved')
        type(self.place).objects.filter(pk=self.place.pk).update(description_ru='New current text')
        response = self.client.get('/ru' + self.url)
        self.assertNotContains(response, 'Сначала верните предложение на доработку.')

    def test_location_codes_are_readable_in_review(self):
        from catalog.services.moderation_changes import describe_change
        with override('ru'):
            change = describe_change('district', 'baku_narimanov', 'baku_nasimi')
        self.assertEqual(change['before_text'], 'Баку, Наримановский район')
        self.assertEqual(change['after_text'], 'Баку, Насиминский район')

    def test_structured_fields_have_human_names(self):
        with override('ru'):
            labels = [moderation_hub.field_label(self.place, key) for key in ['pricing_plans', 'nested_pricing', 'structured_schedule', 'gallery']]
        self.assertEqual(labels, ['Тарифы', 'Тарифы по занятиям', 'Расписание', 'Галерея'])
