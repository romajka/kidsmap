"""Empty coordinates allow normal server-validated manual district persistence."""
from django.test import TestCase
from django.urls import reverse
from catalog.models import VolunteerPlaceRevision
from catalog.services.publication_forms import version_token
from catalog.testcases.test_task33_publication import PublicationFixture


class ManualOwnerLocationTests(PublicationFixture,TestCase):
    def test_manual_baku_district_is_saved_and_reloaded_as_candidate(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('owner_place_edit',args=[self.place.pk]),{
            'form_action':'save_draft','publication_token':version_token(self.place),
            'region':'baku','district':'baku_yasamal','lat':'','lng':'',
            'description_az':self.place.description_az})
        self.assertEqual(response.status_code,302,str(response.context['form'].errors) if response.context else '')
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.payload['district'],'baku_yasamal')
        self.assertIsNone(revision.payload.get('lat'))
        form = self.client.get(reverse('owner_place_edit',args=[self.place.pk])).context['form']
        self.assertEqual(form['region'].value(),'baku')
        self.assertEqual(form['district'].value(),'baku_yasamal')
