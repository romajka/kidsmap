"""Resumable proposals never grant person or document authority."""
from uuid import uuid4
from importlib import import_module
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied,ValidationError
from django.test import TestCase
from django.http import QueryDict
from catalog.models import Specialist

class SpecialistProposalDraftTests(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_user('proposal-entry-author')
        self.other=get_user_model().objects.create_user('proposal-entry-other')
        self.key=uuid4()

    def service(self):
        return import_module('catalog.services.specialist_proposal_drafts')

    def data(self,**values):
        result=QueryDict('',mutable=True)
        result.update({'locations-TOTAL_FORMS':'0','locations-INITIAL_FORMS':'0','locations-MIN_NUM_FORMS':'0','locations-MAX_NUM_FORMS':'30'})
        result.update(values);return result

    def save(self,data=None,version=0,submit=False,files=None):
        return self.service().save_proposal(actor=self.actor,draft_id=self.key,expected_version=str(version),data=data or self.data(),files=files or {},submit=submit)

    def test_empty_first_step_is_resumable_without_a_specialist(self):
        draft=self.save()
        self.assertEqual(draft.version,1);self.assertEqual(Specialist.objects.count(),0)
        loaded=self.service().get_proposal(actor=self.actor,draft_id=self.key)
        self.assertEqual(loaded.pk,draft.pk)

    def test_partial_draft_validates_links_but_defers_submit_completeness(self):
        self.save(self.data(name='QA Partial',consultation_format='offline'))
        with self.assertRaises(ValidationError):self.save(self.data(name='QA Partial',consultation_format='offline'),version=1,submit=True)
        self.assertEqual(Specialist.objects.count(),0)
        with self.assertRaises(ValidationError):self.save(self.data(experience_years='bad'),version=1)
        self.assertEqual(self.service().get_proposal(actor=self.actor,draft_id=self.key).version,1)

    def test_other_actor_cannot_read_or_write(self):
        self.save()
        with self.assertRaises(PermissionDenied):self.service().get_proposal(actor=self.other,draft_id=self.key)
        with self.assertRaises(PermissionDenied):self.service().save_proposal(actor=self.other,draft_id=self.key,expected_version='1',data=self.data(),files={},submit=False)

    def test_stale_draft_cannot_overwrite_and_authority_keys_are_discarded(self):
        self.save(self.data(name='QA Current',verified_person_user=str(self.actor.pk),owner=str(self.actor.pk),document_token='forged'))
        with self.assertRaises(ValidationError) as caught:self.save(self.data(name='QA Stale'),version=0)
        self.assertEqual(caught.exception.code,'stale_version')
        draft=self.service().get_proposal(actor=self.actor,draft_id=self.key)
        self.assertEqual(draft.payload['name'],['QA Current'])
        self.assertNotIn('owner',draft.payload);self.assertNotIn('document_token',draft.payload)

    def test_double_submit_creates_one_author_only_profile(self):
        from catalog.models import SpecialistSpecialization
        spec=SpecialistSpecialization.objects.create(code='proposal-qa',name_ru='QA Direction',name_az='QA',name_en='QA')
        data=self.data(name='QA Proposal',consultation_format='online',bio_ru='QA Bio',phone='+994500000000',language_ru='on',specializations=str(spec.pk))
        first=self.save(data,submit=True);second=self.save(data,submit=True)
        self.assertEqual(first.submitted_specialist_id,second.submitted_specialist_id)
        person=Specialist.objects.get(pk=first.submitted_specialist_id)
        self.assertEqual(person.created_by_id,self.actor.pk);self.assertIsNone(person.owner_id);self.assertIsNone(person.verified_person_user_id)
        self.assertEqual(person.status,'pending')
        with patch('catalog.services.features.is_specialists_section_enabled',return_value=True):
            self.client.force_login(self.actor)
            self.assertEqual(self.client.get(f'/ru/account/specialists/{person.pk}/').status_code,404)
            self.assertEqual(self.client.get(f'/ru/account/specialists/{person.pk}/certificates/').status_code,404)

    def test_private_photo_survives_reload_is_author_only_and_copies_on_send(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.models import SpecialistSpecialization
        stream=BytesIO();Image.new('RGB',(12,12),'green').save(stream,format='PNG')
        draft=self.save(files={'photo':SimpleUploadedFile('qa.png',stream.getvalue(),content_type='image/png')})
        self.addCleanup(draft.photo.storage.delete,draft.photo.name)
        with self.assertRaises(ValueError):_ = draft.photo.url
        url=f'/ru/account/specialists/proposals/{draft.pk}/photo/'
        with patch('catalog.services.features.is_specialists_section_enabled',return_value=True):
            self.client.force_login(self.actor)
            response=self.client.get(url);self.assertEqual(response.status_code,200);self.assertEqual(response['Cache-Control'],'private, no-store')
            self.client.force_login(self.other);self.assertEqual(self.client.get(url).status_code,404)
        spec=SpecialistSpecialization.objects.create(code='proposal-photo-qa',name_ru='QA',name_az='QA',name_en='QA')
        sent=self.save(self.data(name='QA Photo person',consultation_format='online',bio_ru='QA Bio',phone='+994500000000',language_ru='on',specializations=str(spec.pk)),version=1,submit=True)
        person=sent.submitted_specialist
        self.assertTrue(person.photo)
        self.addCleanup(person.photo.storage.delete,person.photo.name)
        self.assertFalse(sent.photo)

    def test_rendered_first_step_save_reload_resume_and_validation_errors(self):
        from django.urls import reverse
        with patch('catalog.services.features.is_specialists_section_enabled',return_value=True):
            self.client.force_login(self.actor)
            url=reverse('specialist_workspace_proposal')
            page=self.client.get(url);self.assertEqual(page.status_code,200)
            data=self.data(name='QA Resume',draft_key=str(page.context['draft_key']),draft_version='0',form_action='save_draft')
            response=self.client.post(url,data);self.assertEqual(response.status_code,302)
            reloaded=self.client.get(response['Location']);self.assertEqual(reloaded.status_code,200)
            self.assertEqual(reloaded.context['form']['name'].value(),'QA Resume')
            data['draft_version']='1';data['form_action']='submit'
            invalid=self.client.post(response['Location'],data);self.assertEqual(invalid.status_code,400)
            self.assertIn('specializations',invalid.context['form'].errors)
            self.assertEqual(invalid.context['form']['name'].value(),'QA Resume')

    def test_unsaved_proposal_parent_accepts_multiple_offline_rows(self):
        from catalog.models import Region
        region=Region.objects.create(key='proposal-entry-region',name_ru='QA',name_az='QA',name_en='QA')
        data=self.data(name='QA Offline',consultation_format='both')
        data['locations-TOTAL_FORMS']='2'
        for i in range(2):data.update({f'locations-{i}-address':f'QA office {i}',f'locations-{i}-region':region.pk,f'locations-{i}-is_active':'on',f'locations-{i}-price_per_session':str(i*35)})
        draft=self.save(data);self.assertEqual(draft.payload['locations-1-price_per_session'],['35'])
