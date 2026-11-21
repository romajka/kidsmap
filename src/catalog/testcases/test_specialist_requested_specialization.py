"""A specialist whose specialty is not in the list can name it instead of picking one."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import QueryDict
from django.test import TestCase

from catalog.testcases.specialist_document_fixtures import portrait_upload
from catalog.forms import OwnerSpecialistForm
from catalog.models import Specialist, SpecialistSpecialization
from catalog.services.specialist_proposal_drafts import _payload


class RequestedSpecializationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.psy, _ = SpecialistSpecialization.objects.get_or_create(
            code='psychologist', defaults={'name': 'psy', 'name_ru': 'psy', 'name_az': 'psy', 'name_en': 'psy'})

    def form(self, **extra):
        data = dict(name='Karate coach', bio_ru='Coaching kids', consultation_format='online',
                    lesson_type='group', lesson_price='25',
                    phone='+994501234567', language_ru='on')
        data.update(extra)
        return OwnerSpecialistForm(data, files={'photo': portrait_upload()})

    def test_neither_a_specialty_nor_an_own_one_is_rejected(self):
        form = self.form()
        self.assertFalse(form.is_valid())
        self.assertIn('specializations', form.errors)

    def test_own_specialty_alone_is_enough_and_is_tidied(self):
        form = self.form(requested_specialization='  Karate   for   kids ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['requested_specialization'], 'Karate for kids')
        person = form.save()
        person.refresh_from_db()
        self.assertEqual(person.requested_specialization, 'Karate for kids')

    def test_own_specialty_can_sit_next_to_a_listed_one(self):
        form = self.form(specializations=[self.psy.pk], requested_specialization='Sand therapy')
        self.assertTrue(form.is_valid(), form.errors)

    def test_draft_payload_keeps_the_own_specialty(self):
        data = QueryDict(mutable=True)
        data.update({'name': 'X', 'requested_specialization': 'Karate'})
        self.assertEqual(_payload(data).get('requested_specialization'), ['Karate'])

    def test_previous_release_can_insert_without_the_new_column(self):
        apps = MigrationExecutor(connection).loader.project_state(
            ('catalog', '0154_workflow_email_delivery_guards')
        ).apps
        previous_model = apps.get_model('catalog', 'Specialist')
        previous = previous_model.objects.create(name='QA Specialist', slug='qa-previous-writer')
        self.assertEqual(Specialist.objects.get(pk=previous.pk).requested_specialization, '')
