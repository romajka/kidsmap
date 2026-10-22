"""Translated display labels must never replace stable submitted nature values."""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.forms import OwnerPlaceEditForm
from catalog.models import Place, VolunteerPlaceRevision
from catalog.models.catalog_structure import PlaceNature
from catalog.services.publication_forms import version_token
from catalog.testcases.test_task33_publication import PublicationFixture


class PlaceNatureLabelsTests(SimpleTestCase):
    def test_runtime_choices_in_all_languages(self):
        for language,labels in [('ru',['Бизнес','Общественное место']),
                                ('az',['Biznes','İctimai məkan']),('en',['Business','Public space'])]:
            with self.subTest(language=language), override(language):
                choices = [(value,str(label)) for value,label in Place._meta.get_field('nature').formfield().choices]
                self.assertEqual(choices,[('', '---------'), *zip(['business','public_space'],labels)])
                self.assertEqual([str(label) for value,label in PlaceNature.choices],labels)

    def test_only_machine_values_validate(self):
        field = Place._meta.get_field('nature').formfield()
        for language in ('ru','az','en'):
            with override(language):
                for value in ('business','public_space'):
                    self.assertEqual(field.clean(value),value)
                for label in ('Biznes','İctimai məkan','Business','Public space','Бизнес','Общественное место'):
                    with self.assertRaises(ValidationError): field.clean(label)


class PlaceNaturePersistenceTests(PublicationFixture,TestCase):
    def test_owner_forged_nature_is_ignored_and_live_stays_unchanged(self):
        self.client.force_login(self.owner)
        original = self.place.nature
        for language,value in [('az','public_space'),('en','business'),('ru','public_space')]:
            self.place.refresh_from_db()
            with override(language):
                url = reverse('owner_place_edit',args=[self.place.pk])
            response = self.client.post(url,{'form_action':'save_draft','nature':value,
                'publication_token':version_token(self.place),'description_az':self.place.description_az})
            self.assertEqual(response.status_code,302, str(response.context['form'].errors) if response.context else '')
            revision = VolunteerPlaceRevision.objects.get(place=self.place)
            self.assertNotIn('nature', revision.payload)
            self.place.refresh_from_db()
            self.assertEqual(self.place.nature,original)
            self.assertNotIn('nature', self.client.get(url).context['form'].fields)
