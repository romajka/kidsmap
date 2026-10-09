"""ORG-06: localized names and safe comparison after canonical version rejection."""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Organization, ServerDraft
from catalog.services import publication


COPY = {
    'ru': ('Название организации (AZ)', 'Изменения уже сохранены в другой вкладке', 'Открыть актуальные данные'),
    'az': ('Təşkilatın adı (AZ)', 'Dəyişikliklər artıq başqa tabda', 'Aktual məlumatları aç'),
    'en': ('Organization name (AZ)', 'Changes have already been saved in another tab', 'Open current data'),
}


class OrganizationFormCopyTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='org06_owner')
        self.other = get_user_model().objects.create_user(username='org06_other')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='ORG06 original')
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.detail = reverse('organization_workspace_detail', args=[self.org.pk])
        response = self.client.get(self.detail)
        self.token = response.context['csrf_token']
        self.data = {'name_az': 'ORG06 Winner A', 'name_ru': 'ORG06 RU', 'name_en': 'ORG06 EN',
                     'description_az': 'ORG06 synthetic description', 'phone': '+994501234567',
                     'whatsapp': '', 'website': 'https://example.invalid/', 'expected_version': 1,
                     'revision_version': 0, 'submit': '1', 'csrfmiddlewaretoken': self.token}

    def save(self, **fields):
        return self.client.post(reverse('organization_workspace_save', args=[self.org.pk]), {**self.data, **fields})

    def test_create_required_error_label_is_localized_and_preserves_input(self):
        count = Organization.objects.count()
        for lang, (label, _, _) in COPY.items():
            with self.subTest(lang=lang), override(lang):
                response = self.client.post(reverse('organization_workspace_create'), {**self.data, 'name_az': ''})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(str(response.context['create_form'].fields['name_az'].label), label)
                self.assertContains(response, label, status_code=400)
                self.assertNotContains(response, 'Name az', status_code=400)
                self.assertEqual(response.context['create_form']['phone'].value(), self.data['phone'])
        self.assertEqual(Organization.objects.count(), count)

    def test_all_visible_and_hidden_form_labels_use_current_language(self):
        expected = {'ru': ('Название организации (RU)', 'Телефон', 'Версия карточки', 'Версия изменений'),
                    'az': ('Təşkilatın adı (RU)', 'Telefon', 'Kartın versiyası', 'Dəyişikliklərin versiyası'),
                    'en': ('Organization name (RU)', 'Phone', 'Card version', 'Changes version')}
        for lang, labels in expected.items():
            with self.subTest(lang=lang), override(lang):
                form = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk])).context['candidate_form']
                for name, label in zip(('name_ru', 'phone', 'expected_version', 'revision_version'), labels):
                    self.assertEqual(str(form.fields[name].label), label)

    def test_repeated_conflict_preserves_loser_winner_and_original_cas_in_each_language(self):
        self.assertEqual(self.save().status_code, 302)
        for lang, (_, message, link) in COPY.items():
            with self.subTest(lang=lang), override(lang):
                for _ in range(2):
                    response = self.save(name_az='ORG06 Loser B')
                    self.assertEqual(response.status_code, 409)
                    self.assertContains(response, message, status_code=409)
                    self.assertNotContains(response, 'Candidate version conflict.', status_code=409)
                    self.assertContains(response, link, status_code=409)
                    self.assertContains(response, '?current=1', status_code=409)
                    form = response.context['candidate_form']
                    self.assertEqual(form['name_az'].value(), 'ORG06 Loser B')
                    self.assertEqual(form['revision_version'].value(), '0')
                    self.assertEqual(form.non_field_errors().as_data()[0].code, 'candidate_version_conflict')
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az, 'ORG06 original')
        self.assertEqual(self.org.content_revision.payload['name_az'], 'ORG06 Winner A')
        self.assertEqual(self.org.content_revision.version, 1)

    def test_current_view_compares_winner_without_deleting_private_draft(self):
        self.assertEqual(self.save().status_code, 302)
        draft = ServerDraft.objects.create(actor=self.owner, target_type='organization', target_id=self.org.pk,
                                          source_version=1, fields={'name_az': 'ORG06 private B'})
        current = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]) + '?current=1')
        self.assertEqual(current.context['candidate_form']['name_az'].value(), 'ORG06 Winner A')
        self.assertContains(current, 'data-org-current-data')
        normal = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        self.assertEqual(normal.context['candidate_form']['name_az'].value(), 'ORG06 private B')
        draft.refresh_from_db()
        self.assertEqual(draft.fields, {'name_az': 'ORG06 private B'})
        self.assertEqual(draft.version, 1)
        self.assertEqual(self.save(name_az='ORG06 Loser B').status_code, 409)

    def test_canonical_rejection_has_code_and_unchanged_message_without_mutation(self):
        for schema, version, candidate, code, message in (
            (0, 1, 0, 'publication_schema_conflict', 'Publication schema conflict.'),
            (publication.SCHEMA_VERSION, 0, 0, 'publication_source_conflict', 'Publication source conflict.'),
            (publication.SCHEMA_VERSION, 1, 1, 'candidate_version_conflict', 'Candidate version conflict.'),
        ):
            with self.subTest(code=code):
                with self.assertRaises(ValidationError) as raised:
                    publication.propose(actor=self.owner, target_type='organization', target_id=self.org.pk,
                                        patch={'name_az': 'ORG06 Blocked'}, schema_version=schema,
                                        expected_version=version, revision_version=candidate)
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(raised.exception.messages, [message])
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az, 'ORG06 original')
        self.assertFalse(hasattr(self.org, 'content_revision'))

    def test_conflict_codes_are_localized_unknown_detail_does_not_leak(self):
        codes = ('publication_schema_conflict', 'publication_source_conflict', 'candidate_version_conflict',
                 'candidate_dependency_conflict', 'candidate_source_conflict', 'unknown_detail')
        for lang in COPY:
            with override(lang):
                for code in codes:
                    with self.subTest(lang=lang, code=code), patch('catalog.controllers.organization_workspace.publication.propose', side_effect=ValidationError('ORG06 technical detail', code=code)):
                        response = self.save(name_az='ORG06 Bound B')
                        self.assertEqual(response.status_code, 409)
                        self.assertNotContains(response, 'ORG06 technical detail', status_code=409)
                        self.assertEqual(response.context['candidate_form']['name_az'].value(), 'ORG06 Bound B')
                        self.assertEqual(response.context['candidate_form'].non_field_errors().as_data()[0].code, code)

    def test_real_dependency_conflict_keeps_candidate_and_bound_input(self):
        self.assertEqual(self.save().status_code, 302)
        Organization.objects.filter(pk=self.org.pk).update(ownership_version=2)
        response = self.save(name_az='ORG06 blocked dependency B', revision_version=1)
        self.assertEqual(response.status_code, 409)
        form = response.context['candidate_form']
        self.assertEqual(form.non_field_errors().as_data()[0].code, 'candidate_dependency_conflict')
        self.assertEqual(form['name_az'].value(), 'ORG06 blocked dependency B')
        self.org.refresh_from_db()
        self.assertEqual(self.org.content_revision.version, 1)
        self.assertEqual(self.org.content_revision.payload['name_az'], 'ORG06 Winner A')
        self.assertEqual(self.org.name_az, 'ORG06 original')

    def test_real_candidate_source_conflict_does_not_overwrite_external_live_change(self):
        self.assertEqual(self.save().status_code, 302)
        # Simulate a separate legacy producer changing a live field without advancing content_version.
        Organization.objects.filter(pk=self.org.pk).update(name_az='ORG06 external live change')
        response = self.save(name_az='ORG06 blocked source B', revision_version=1)
        self.assertEqual(response.status_code, 409)
        form = response.context['candidate_form']
        self.assertEqual(form.non_field_errors().as_data()[0].code, 'candidate_source_conflict')
        self.assertEqual(form['name_az'].value(), 'ORG06 blocked source B')
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az, 'ORG06 external live change')
        self.assertEqual(self.org.content_revision.version, 1)
        self.assertEqual(self.org.content_revision.payload['name_az'], 'ORG06 Winner A')

    def test_foreign_current_view_and_post_and_missing_csrf_remain_denied(self):
        self.client.force_login(self.other)
        for suffix in ('', '?current=1'):
            response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]) + suffix)
            self.assertEqual(response.status_code, 404)
            self.assertNotContains(response, 'ORG06 original', status_code=404)
        self.assertEqual(self.save().status_code, 404)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        data = {k: v for k, v in self.data.items() if k != 'csrfmiddlewaretoken'}
        self.assertEqual(client.post(reverse('organization_workspace_save', args=[self.org.pk]), data).status_code, 403)
