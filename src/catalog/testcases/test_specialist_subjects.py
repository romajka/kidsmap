from django.test import TestCase
from django.utils.translation import override

from catalog.forms import OwnerSpecialistForm
from catalog.models import SiteSettings, Specialist, SpecialistSpecialization
from catalog.services.specialist_proposal_drafts import proposal_forms, _payload
from django.http import QueryDict


class SpecialistSubjectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        cls.specs = {}
        for code in ('tutor', 'math_tutor', 'english_teacher', 'exam_prep_tutor', 'psychologist'):
            cls.specs[code], _ = SpecialistSpecialization.objects.get_or_create(
                code=code, defaults={'name': code, 'name_ru': code, 'name_az': code, 'name_en': code})
        cls.math = cls.person('Math teacher', ['math_tutor'], language_en=True)
        cls.english = cls.person('English teacher', ['english_teacher'], language_ru=True)
        cls.both = cls.person('Two subjects', ['tutor', 'math_tutor', 'english_teacher'])
        cls.person('Psychologist', ['psychologist'])
        cls.person('Draft English', ['english_teacher'], status='draft')
        cls.person('Inactive English', ['english_teacher'], is_active=False)

    @classmethod
    def person(cls, name, codes, **kwargs):
        kwargs.setdefault('status', 'published')
        p = Specialist.objects.create(name=name, consultation_format='online', **kwargs)
        p.specializations.set([cls.specs[c] for c in codes])
        return p

    def results(self, **query):
        response = self.client.get('/ru/specialists/', query)
        self.assertEqual(response.status_code, 200)
        return response, {p.pk for p in response.context['page_obj']}

    def test_tutor_category_includes_precise_legacy_subjects_once(self):
        page, ids = self.results(specialization='tutor')
        self.assertEqual(ids, {self.math.pk, self.english.pk, self.both.pk})
        self.assertEqual(page.context['page_obj'].paginator.count, 3)

    def test_subject_filters_real_subject_not_working_language(self):
        _, ids = self.results(specialization='tutor', subject='english_teacher')
        self.assertEqual(ids, {self.english.pk, self.both.pk})
        _, ids = self.results(subject='math_tutor', language='en')
        self.assertEqual(ids, {self.math.pk})

    def test_subject_combines_with_age_price_and_sort_without_redirect(self):
        self.math.age_from = 12
        self.math.price_from = 30
        self.math.save()
        self.both.age_to = 8
        self.both.price_from = 50
        self.both.save()
        page, ids = self.results(subject='math_tutor', age_from='13', age_to='15', price_to='40', sort='price_asc')
        self.assertEqual(ids, {self.math.pk})
        self.assertEqual(page.context['selected']['subject'], 'math_tutor')

    def test_subject_does_not_ignore_other_category_or_unknown_value(self):
        self.assertEqual(self.results(specialization='psychologist', subject='english_teacher')[1], set())
        self.assertEqual(self.results(subject='not-a-subject')[1], set())

    def test_tutor_count_uses_distinct_profiles(self):
        page, _ = self.results()
        tutor = next(x for x in page.context['filter_options'].specializations if x['value'] == 'tutor')
        self.assertEqual(tutor['count'], 3)

    def form(self, codes, **kwargs):
        data = dict(name='Tutor', bio_ru='Teaching', consultation_format='online',
                    phone='+994501234567', language_ru='on', specializations=[self.specs[c].pk for c in codes])
        return OwnerSpecialistForm(data, **kwargs)

    def test_general_tutor_and_exam_prep_require_subject_on_submission(self):
        for code in ('tutor', 'exam_prep_tutor'):
            form = self.form([code])
            self.assertFalse(form.is_valid())
            self.assertIn('specializations', form.errors)

    def test_incomplete_tutor_draft_and_other_category_stay_valid(self):
        for form in (self.form(['tutor'], draft_save_only=True), self.form(['psychologist'])):
            self.assertTrue(form.is_valid(), form.errors)

    def test_multiple_subjects_save_and_reopen_without_loss(self):
        form = self.form(['tutor', 'english_teacher', 'math_tutor'])
        self.assertTrue(form.is_valid(), form.errors)
        person = form.save()
        reopened = OwnerSpecialistForm(instance=person)
        self.assertEqual(set(reopened['specializations'].value()),
                         {self.specs[c].pk for c in ('tutor', 'english_teacher', 'math_tutor')})

    def test_proposal_payload_keeps_multiple_subjects(self):
        data = QueryDict('', mutable=True)
        values = [str(self.specs[c].pk) for c in ('tutor', 'english_teacher', 'math_tutor')]
        data.setlist('specializations', values)
        from django.contrib.auth import get_user_model
        actor = get_user_model().objects.create_user('subject-applicant')
        form, _ = proposal_forms(actor=actor, payload=_payload(data))
        self.assertEqual(form['specializations'].value(), values)

    def test_admin_requires_subject_for_pending_and_published_but_allows_draft(self):
        from catalog.domain_admin.specialist import SpecialistAdminForm
        for status in ('draft', 'pending', 'published'):
            form = SpecialistAdminForm(data={
                'name': 'Admin tutor', 'status': status, 'consultation_format': 'online',
                'specializations': [self.specs['tutor'].pk],
            })
            self.assertEqual(form.is_valid(), status == 'draft', form.errors)
            if status != 'draft':
                self.assertIn('specializations', form.errors)

    def test_group_picker_and_subject_picker_do_not_duplicate_fields(self):
        from catalog.controllers.specialist_workspace import _build_grouped_specializations
        form = OwnerSpecialistForm(instance=self.both)
        groups = _build_grouped_specializations(form)
        self.assertEqual(groups[0]['items'][0]['code'], 'tutor')
        category_codes = {item['code'] for group in groups for item in group['items']}
        self.assertIn('tutor', category_codes)
        self.assertNotIn('english_teacher', category_codes)
        self.assertNotIn('math_tutor', category_codes)
        options = {item['value']: item for item in form.subject_options}
        self.assertTrue(options['english_teacher']['widget'].data['selected'])
        self.assertTrue(options['math_tutor']['widget'].data['selected'])

    def test_subject_seed_is_idempotent_and_does_not_overwrite_admin_changes(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection
        seed = import_module('catalog.migrations.0153_specialist_school_subjects').seed_subjects
        physics, _ = SpecialistSpecialization.objects.get_or_create(code='physics_tutor')
        physics.name_ru = 'Custom title'
        physics.is_active = False
        physics.save()
        seed(apps, SimpleNamespace(connection=connection))
        seed(apps, SimpleNamespace(connection=connection))
        physics.refresh_from_db()
        self.assertEqual(physics.name_ru, 'Custom title')
        self.assertFalse(physics.is_active)
        self.assertEqual(SpecialistSpecialization.objects.filter(code='physics_tutor').count(), 1)

    def test_subject_is_prominent_and_localized(self):
        for lang, label in [('ru', 'Математика'), ('az', 'Riyaziyyat'), ('en', 'Mathematics')]:
            with override(lang):
                url = '/specialists/' if lang == 'az' else f'/{lang}/specialists/'
                page = self.client.get(url, {'subject': 'math_tutor'})
                self.assertContains(page, 'name="subject"')
                self.assertContains(page, label)
                self.assertContains(page, 'km-subject-tags')

    def test_tutor_discovery_is_one_block_and_reset_clears_subject(self):
        from urllib.parse import parse_qs, urlparse
        page, _ = self.results(specialization='tutor', subject='english_teacher', language='ru')
        self.assertContains(page, 'class="km-subject-discovery"', count=1)
        self.assertNotContains(page, 'catalog-hero-tags-label')
        self.assertEqual(page.context['specialization_chips'][0]['value'], 'tutor')
        self.assertEqual(parse_qs(urlparse(page.context['all_specializations_url']).query), {'language': ['ru']})
        self.assertEqual(parse_qs(urlparse(page.context['all_tutors_url']).query), {'specialization': ['tutor'], 'language': ['ru']})

    def test_owner_and_admin_share_subject_requirements(self):
        from catalog.domain_admin.specialist import SpecialistAdminForm
        owner = OwnerSpecialistForm()
        admin = SpecialistAdminForm()
        self.assertEqual(owner.subject_rules, admin.subject_rules)
        self.assertIn(str(self.specs['tutor'].pk), admin.subject_rules['requires'])
        self.assertIn(str(self.specs['math_tutor'].pk), admin.subject_rules['subjects'])

    def test_admin_bulk_moderation_cannot_bypass_required_subject(self):
        from unittest.mock import patch
        from django.contrib import admin
        from django.test import RequestFactory
        from catalog.domain_admin.specialist import SpecialistAdmin
        broken = self.person('Incomplete tutor', ['tutor'], status='draft')
        valid = self.person('Complete tutor', ['tutor', 'math_tutor'], status='draft')
        model_admin = SpecialistAdmin(Specialist, admin.site)
        request = RequestFactory().post('/')
        from django.contrib.auth import get_user_model
        request.user = get_user_model().objects.create_superuser('bulk-subject-reviewer', password='synthetic')
        with patch.object(model_admin, '_require_moderation_permission'), patch.object(model_admin, 'message_user'):
            for action, status in [('mark_pending', 'pending'), ('mark_published', 'published')]:
                getattr(model_admin, action)(request, Specialist.objects.filter(pk__in=[broken.pk, valid.pk]))
                broken.refresh_from_db()
                valid.refresh_from_db()
                self.assertEqual(broken.status, 'draft')
                self.assertEqual(valid.status, status)

    def test_failed_admin_publication_displays_persisted_status(self):
        from django.contrib.auth import get_user_model
        editor = get_user_model().objects.create_superuser('subject-status-admin', password='local-test')
        self.client.force_login(editor)
        person = self.person('Pending tutor', ['tutor', 'math_tutor'], status='pending')
        url = f'/admin/catalog/specialist/{person.pk}/change/'
        page = self.client.get(url)
        data = {'name': person.name, 'status': 'published', 'is_active': 'on',
                'consultation_format': 'online', 'expected_updated_at': person.updated_at.isoformat(),
                'specializations': [self.specs['tutor'].pk]}
        for inline in page.context['inline_admin_formsets']:
            for field in inline.formset.management_form:
                data[field.html_name] = field.value()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('specializations', response.context['adminform'].form.errors)
        person.refresh_from_db()
        self.assertEqual(person.status, 'pending')
        self.assertFalse(response.context['specialist_public_visible'])
        self.assertEqual(response.context['specialist_saved_status'], 'pending')

    def test_search_finds_subject_even_when_name_and_bio_do_not_mention_it(self):
        for query in ('математика', 'Mathematics', 'Riyaziyyat'):
            with self.subTest(query=query):
                _, ids = self.results(q=query)
                self.assertEqual(ids, {self.math.pk, self.both.pk})
