"""A usable map point is mandatory for new physical-place publication."""
from dataclasses import replace

from django.test import SimpleTestCase

from catalog.services.place_readiness import PlaceReadinessData, evaluate_readiness


class CoordinateReadinessContractTests(SimpleTestCase):
    def ready_data(self, **changes):
        return replace(PlaceReadinessData(
            name_az='Ailə məkanı', description_az='Uşaqlar üçün oyun məkanı.',
            category_code='FUN', subcategory_id=1, subcategory_category_code='FUN',
            district='baku_nasimi', address='Bakı, küçə 12', lat=40.4, lng=49.8,
            age_from=0, age_to=18, price_mode='free', phone1='+994501112233',
            schedule_mode='always_open', has_main_photo=False,
        ), **changes)

    def test_missing_or_partial_coordinates_block_readiness_and_full_progress(self):
        for lat, lng in ((None,None),(None,49.8),(40.4,None)):
            with self.subTest(lat=lat,lng=lng):
                readiness=evaluate_readiness(self.ready_data(lat=lat,lng=lng))
                self.assertFalse(readiness.is_ready)
                self.assertLess(readiness.percentage,100)
                self.assertIn('missing_coordinates',readiness.quality_codes)

    def test_nonfinite_and_out_of_range_coordinates_are_rejected(self):
        for lat,lng in ((float('nan'),49.8),(40.4,float('nan')),(float('inf'),49.8),
                        (40.4,float('-inf')),(91,0),(-91,0),(0,181),(0,-181)):
            with self.subTest(lat=lat,lng=lng):
                self.assertIn('invalid_coordinates',evaluate_readiness(self.ready_data(lat=lat,lng=lng)).quality_codes)

    def test_zero_and_range_boundaries_are_valid_and_photo_stays_optional(self):
        for lat,lng in ((0,0),(-90,-180),(90,180),(40.4,49.8)):
            with self.subTest(lat=lat,lng=lng):
                readiness=evaluate_readiness(self.ready_data(lat=lat,lng=lng))
                self.assertTrue(readiness.is_ready)
                self.assertEqual(readiness.percentage,100)
                self.assertIn('coordinates',[item.code for item in readiness.items])
                self.assertNotIn('photo',[item.code for item in readiness.items])


from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services import publication
from catalog.testcases.utils import create_ready_place


class CoordinatePublicationIngressTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user('coordinate-owner')
        self.admin=get_user_model().objects.create_superuser('coordinate-admin','','synthetic')
        self.place=create_ready_place(owner=self.owner,created_by=self.owner)

    def propose(self,patch,submit=True,revision_version=0):
        self.place.refresh_from_db()
        return publication.propose(actor=self.owner,target_type='place',target_id=self.place.pk,
            patch=patch,schema_version=publication.SCHEMA_VERSION,expected_version=self.place.content_version,
            revision_version=revision_version,submit=submit,explicit_save=True)

    def set_unpublished_without_point(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False,lat=None,lng=None)
        self.place.refresh_from_db()

    def test_service_submission_requires_point_but_draft_still_saves(self):
        self.set_unpublished_without_point()
        with self.assertRaises(ValidationError):self.propose({'description_az':'Yeni təsvir'})
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
        revision=self.propose({'description_az':'Yeni təsvir'},submit=False)
        self.assertEqual(revision.status,'draft')

    def test_partial_patch_uses_existing_point(self):
        revision=self.propose({'description_az':'Yeni təsvir'})
        self.assertEqual(revision.status,'pending')

    def test_pending_point_is_preserved_when_submitting_partial_patch(self):
        self.set_unpublished_without_point()
        revision=self.propose({'lat':40.4,'lng':49.8},submit=False)
        revision=self.propose({'description_az':'Yeni təsvir'},revision_version=revision.version)
        self.assertEqual(revision.status,'pending')
        self.assertEqual(revision.payload['lat'],40.4)

    def test_live_point_cannot_be_removed_on_submit(self):
        with self.assertRaises(ValidationError):self.propose({'lat':None,'lng':None})
        self.place.refresh_from_db()
        self.assertIsNotNone(self.place.lat)

    def test_approval_of_saved_candidate_cannot_remove_live_point(self):
        revision=self.propose({'lat':None,'lng':None},submit=False)
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='pending')
        with self.assertRaises(ValidationError):
            publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        self.place.refresh_from_db()
        self.assertIsNotNone(self.place.lat)

    def test_legacy_live_requires_point_for_new_actions_but_stays_visible(self):
        Place.objects.filter(pk=self.place.pk).update(lat=None,lng=None)
        with self.assertRaises(ValidationError):self.propose({'description_az':'Yeni təsvir'})
        self.place.refresh_from_db()
        with self.assertRaises(ValidationError):
            publication.publish(actor=self.admin,place_id=self.place.pk,expected_version=self.place.content_version)
        revision=self.propose({'description_az':'Yeni təsvir'},submit=False)
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='pending')
        with self.assertRaises(ValidationError):
            publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
        from catalog.services.content_quality import public_place_queryset
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())
        self.assertIsNone(self.place.lat)

    def test_new_publication_and_legacy_pending_approval_require_point(self):
        self.set_unpublished_without_point()
        with self.assertRaises(ValidationError):
            publication.publish(actor=self.admin,place_id=self.place.pk,expected_version=self.place.content_version)
        revision=self.propose({'description_az':'Yeni təsvir'},submit=False)
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='pending')
        with self.assertRaises(ValidationError):
            publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_active)

    def test_admin_live_ordinary_save_cannot_bypass_point_requirement(self):
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.testcases.place_readiness import PlaceAdminFormReadinessTests
        Place.objects.filter(pk=self.place.pk).update(lat=None,lng=None)
        self.place.refresh_from_db()
        data=PlaceAdminFormReadinessTests()._payload(self.place,lat='',lng='')
        form=PlaceAdminForm(data=data,instance=self.place)
        self.assertFalse(form.is_valid())
        self.assertIn('lat',form.errors)
        self.assertFalse(form.place_readiness_compatibility)

    def test_owner_submit_form_requires_point_but_draft_allows_it(self):
        from django import forms
        from catalog.forms import OwnerPlaceEditForm
        from catalog.services.volunteer_places import editor_form
        self.set_unpublished_without_point()
        source=editor_form(self.place)
        data={name:source[name].value() if source[name].value() is not None else ''
              for name,field in source.fields.items() if not isinstance(field,forms.FileField)}
        data['offers_adult_classes']='0'
        form=OwnerPlaceEditForm(data={**data,'action':'submit'},instance=self.place,submit_for_moderation=True)
        self.assertFalse(form.is_valid())
        self.assertIn('lat',form.errors)
        self.place.refresh_from_db()
        draft=OwnerPlaceEditForm(data={**data,'action':'draft'},instance=self.place,draft_save_only=True)
        self.assertTrue(draft.is_valid(),str(draft.errors))

    def test_volunteer_submit_returns_field_error_without_pending_or_storage_writes(self):
        from django import forms
        from django.contrib.auth.models import Group
        from django.core.files.storage import default_storage
        from django.urls import reverse
        from unittest.mock import patch
        from catalog.services.volunteer_places import editor_form
        self.set_unpublished_without_point()
        self.owner.is_staff=True
        self.owner.save(update_fields=['is_staff'])
        self.owner.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        Place.objects.filter(pk=self.place.pk).update(owner=None)
        self.place.refresh_from_db()
        source=editor_form(self.place)
        data={name:source[name].value() if source[name].value() is not None else ''
              for name,field in source.fields.items() if not isinstance(field,forms.FileField)}
        data['action']='submit'
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        image=BytesIO()
        Image.new('RGB',(40,40),'green').save(image,format='PNG')
        uploaded=SimpleUploadedFile('coordinate-submit.png',image.getvalue(),content_type='image/png')
        self.client.force_login(self.owner)
        with patch.object(default_storage,'save') as storage_save:
            response=self.client.post(reverse('admin:volunteer_edit',args=[self.place.pk]),{**data,'photo':uploaded})
            self.assertEqual(response.status_code,200)
            self.assertIn('lat',response.context['form'].errors)
            self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
            storage_save.assert_not_called()
        data['action']='draft'
        response=self.client.post(reverse('admin:volunteer_edit',args=[self.place.pk]),data)
        self.assertEqual(response.status_code,302)
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).status,'draft')
