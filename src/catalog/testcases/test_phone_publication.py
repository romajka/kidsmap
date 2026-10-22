from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from catalog.models import Place, Organization
from catalog.services.publication import _validate_patch


class PhonePublicationValidationTests(SimpleTestCase):
    def test_normalizes_changed_call_and_whatsapp(self):
        place=Place(phone1='+994504274393')
        patch=_validate_patch(place,'place',{'phone1':'+1 (310) 456-4918',
            'whatsapp_mode':'separate','whatsapp_number':'https://wa.me/905321234567'})
        self.assertEqual(patch['phone1'],'+13104564918')
        self.assertEqual(patch['whatsapp_number'],'+905321234567')
        self.assertEqual(place.phone1,'+994504274393')

    def test_invalid_changed_phone_rejected_even_direct_patch(self):
        with self.assertRaises(ValidationError):_validate_patch(Place(),'place',{'phone1':'+994 13 104 56 49'})

    def test_unchanged_invalid_legacy_phone_preserved(self):
        old='+994 13 104 56 49'
        self.assertEqual(_validate_patch(Place(phone1=old),'place',{'phone1':old})['phone1'],old)

    def test_separate_requires_number_and_rejects_arbitrary_url(self):
        for patch in [{'whatsapp_mode':'separate'}, {'whatsapp_mode':'separate','whatsapp_number':'https://evil.invalid/13104564918'}]:
            with self.subTest(patch=patch),self.assertRaises(ValidationError):_validate_patch(Place(),'place',patch)

    def test_disabled_whatsapp_preserves_stored_number(self):
        place=Place(whatsapp_mode='separate',whatsapp_number='+13104564918')
        self.assertEqual(_validate_patch(place,'place',{'whatsapp_mode':'none'}),{'whatsapp_mode':'none'})
        self.assertEqual(place.whatsapp_number,'+13104564918')

    def test_selected_country_and_unknown_region(self):
        result=_validate_patch(Place(),'place',{'phone_country':'US','phone1':'(310) 456-4918'})
        self.assertEqual(result['phone1'],'+13104564918')
        with self.assertRaises(ValidationError):_validate_patch(Place(),'place',{'phone_country':'XX'})

    def test_organization_patch_uses_same_validation(self):
        result=_validate_patch(Organization(),'organization',{'phone':'+90 (532) 123-45-67','whatsapp':'https://wa.me/13104564918'})
        self.assertEqual(result['phone'],'+905321234567')
        self.assertEqual(result['whatsapp'],'+13104564918')

from django.test import TestCase
from django.contrib.auth import get_user_model
from catalog.services import publication
from catalog.testcases.utils import create_quality_place


class PhonePublicationLifecycleTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='phone_owner')
        self.staff=get_user_model().objects.create_superuser(username='phone_staff',email='phone@example.invalid',password='synthetic')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner,phone1='+994504274393')

    def propose(self,patch,revision_version=0):
        self.place.refresh_from_db()
        return publication.propose(actor=self.owner,target_type='place',target_id=self.place.pk,
            patch=patch,schema_version=1,expected_version=self.place.content_version,
            revision_version=revision_version,submit=True)

    def test_pending_separate_contacts_never_replace_live_before_approval(self):
        revision=self.propose({'phone1':'+90 (532) 123-45-67','whatsapp_mode':'separate','whatsapp_number':'https://wa.me/13104564918'})
        self.place.refresh_from_db()
        self.assertEqual(self.place.phone1,'+994504274393')
        self.assertEqual(self.place.whatsapp_mode,'legacy')
        self.assertEqual(revision.payload['phone1'],'+905321234567')
        publication.review(actor=self.staff,revision_id=revision.pk,version=revision.version,approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.phone1,'+905321234567')
        self.assertEqual(self.place.whatsapp_number,'+13104564918')
        self.assertEqual(self.place.whatsapp_mode,'separate')

    def test_reject_keeps_live_and_partial_edit_retains_pending_whatsapp(self):
        revision=self.propose({'whatsapp_mode':'separate','whatsapp_number':'+13104564918'})
        revision=self.propose({'whatsapp_mode':'separate','description_ru':'Обновлённое описание'},revision.version)
        self.assertEqual(revision.payload['whatsapp_number'],'+13104564918')
        publication.review(actor=self.staff,revision_id=revision.pk,version=revision.version,approve=False,note='Уточните контакт')
        self.place.refresh_from_db()
        self.assertEqual(self.place.whatsapp_number,'')
        self.assertEqual(self.place.whatsapp_mode,'legacy')

    def test_whatsapp_only_counts_for_readiness_and_public_queryset(self):
        from catalog.services.place_readiness import effective_contact
        from catalog.services.content_quality import published_place_queryset
        Place.objects.filter(pk=self.place.pk).update(phone1='',website='',whatsapp_mode='separate',whatsapp_number='+13104564918')
        self.place.refresh_from_db()
        self.assertIn('+13104564918',effective_contact(self.place))
        self.assertTrue(published_place_queryset(Place.objects.all()).filter(pk=self.place.pk).exists())
        self.place.whatsapp_mode='none'
        self.assertEqual(effective_contact(self.place),'')
