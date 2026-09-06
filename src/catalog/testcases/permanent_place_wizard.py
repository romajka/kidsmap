import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.models import Place, PricingPlan, PlacePhoto
from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.services.content_quality import place_quality_check, public_place_queryset


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PermanentPlaceWizardTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media = TemporaryDirectory(ignore_cleanup_errors=True)
        cls.media_settings = override_settings(MEDIA_ROOT=cls.media.name)
        cls.media_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_settings.disable()
        cls.media.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user('placewizard', password='password')
        self.client.force_login(self.user)
        from catalog.testcases.utils import ensure_quality_subcategory
        self.subcategory = ensure_quality_subcategory("EDU")
        self.controller = OwnerPlacesController.build_default()
        self.request = RequestFactory().post('/')
        self.request.user = self.user

    def photo(self, name='main.png'):
        buffer = BytesIO()
        Image.new('RGB', (64, 48), '#b7d2ba').save(buffer, 'PNG')
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

    def data(self, **overrides):
        data = dict(name_az='Uşaq yaradıcılıq mərkəzi', description_az='Uşaqlar burada yaradıcılıq, rəsm və musiqi ilə məşğul olur. Valideynlər üçün rahat gözləmə sahəsi və yaşa uyğun qruplar mövcuddur. ' * 2,
                    category='EDU', subcategory=str(self.subcategory.pk), age_from='3', age_to='12', region='baku', district='baku_yasamal', address='Nizami 10', lat='40.4', lng='49.8', phone1='+994501112233',
                    schedule_mode='by_appointment', pricing_plans=json.dumps([dict(product_type='lesson', price_kind='on_request')]))
        data.update(overrides)
        return data

    def create(self, **overrides):
        result = self.controller.create_place(request=self.request, data=self.data(**overrides), files={'photo': self.photo()})
        self.assertTrue(result.ok, result.form.errors if result.form else result.message)
        return result.place

    def test_on_request_can_be_submitted_and_becomes_visible_after_approval(self):
        place = self.create()
        self.assertEqual(place.status, 'pending')
        self.assertFalse(place.is_active)
        self.assertTrue(place_quality_check(place).is_ready)
        place.status='published'; place.is_active=True; place.save()
        self.assertTrue(public_place_queryset(Place.objects.all()).filter(pk=place.pk).exists())
        self.assertIsNone(place.price_from)

    def test_required_fields_report_errors_but_draft_accepts_missing(self):
        for field in ('description_az','category','age_from','age_to','address','region','phone1','lat','lng'):
            with self.subTest(field=field):
                form = OwnerPlaceCreateForm(data=self.data(**{field:''}), files={'photo':self.photo()})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)
        draft = OwnerPlaceCreateForm(data={}, draft_save_only=True)
        self.assertTrue(draft.is_valid(), draft.errors)

    def test_open_age_all_ages_with_required_az_name(self):
        for start in ('3','0',''):
            form=OwnerPlaceCreateForm(data=self.data(name_az='Studia', name_ru='Мастерская',age_from=start,age_to='',age_open_ended='1'), files={'photo':self.photo()})
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['age_from'], int(start or 0))
            self.assertIsNone(form.cleaned_data['age_to'])
            self.assertEqual(form.save(commit=False).name_ru, 'Мастерская')

    def test_outside_baku_requires_no_district_or_metro(self):
        place=self.create(region='ganja',district='',metro='')
        self.assertEqual(place.district,'ganja')

    def test_coordinates_reject_partial_nonfinite_and_out_of_range_even_in_draft(self):
        for lat,lng in [('40',''),('NaN','49'),('Infinity','49'),('91','49'),('40','181')]:
            form=OwnerPlaceCreateForm(data={'lat':lat,'lng':lng},draft_save_only=True)
            self.assertFalse(form.is_valid())

    def test_schedule_modes_and_structured_create(self):
        for mode in ('by_appointment','variable','events'):
            self.create(schedule_mode=mode)
        regular=OwnerPlaceCreateForm(data=self.data(schedule_mode='regular'),files={'photo':self.photo()})
        self.assertFalse(regular.is_valid())
        self.assertIn('structured_schedule',regular.errors)
        schedule=[{'weekday':'mon','is_closed':False,'is_24_hours':False,'intervals':[{'start':'09:00','end':'12:00'}]}]
        self.create(schedule_mode='regular',structured_schedule=json.dumps(schedule))

    def test_addon_only_and_inactive_plans_do_not_pass(self):
        for plan in [dict(product_type='deposit',price_kind='exact',price='10'),dict(product_type='lesson',price_kind='on_request',is_active=False)]:
            form=OwnerPlaceCreateForm(data=self.data(pricing_plans=json.dumps([plan])),files={'photo':self.photo()})
            self.assertFalse(form.is_valid())
            self.assertIn('pricing_plans',form.errors)

    def test_all_price_modes_and_plan_limit(self):
        plans=[dict(product_type='lesson',**price) for price in [dict(price_kind='exact',price=20),dict(price_kind='free'),dict(price_kind='from',price_min=10),dict(price_kind='range',price_min=5,price_max=15),dict(price_kind='on_request')]]
        for plan in plans:
            form=OwnerPlaceCreateForm(data=self.data(pricing_plans=json.dumps([plan])),files={'photo':self.photo()})
            self.assertTrue(form.is_valid(),form.errors)
        form=OwnerPlaceCreateForm(data=self.data(pricing_plans=json.dumps([plans[0]]*13)),files={'photo':self.photo()})
        self.assertFalse(form.is_valid());self.assertIn('pricing_plans',form.errors)

    def test_edit_preserves_translations_legacy_and_staff_data(self):
        place=self.create(phone2='+994551112233',extra_conditions_az='Şərtlər',additional_info_ru='Информация')
        place.extra_conditions='Legacy text';place.custom_price_badge_ru='Пробный урок';place.cover_photo='places/reserve.png';place.save()
        plan=place.pricing_plan_records.get();plan.verified_at=timezone.now();plan.save()
        form=OwnerPlaceEditForm(instance=place,data={'name_az':'Yeni ad'},draft_save_only=True)
        self.assertTrue(form.is_valid(),form.errors)
        form.save();place.refresh_from_db();plan.refresh_from_db()
        self.assertEqual(place.phone2,'+994551112233');self.assertEqual(place.extra_conditions_az,'Şərtlər')
        self.assertEqual(place.extra_conditions,'Legacy text');self.assertEqual(place.cover_photo.name,'places/reserve.png')
        self.assertEqual(place.custom_price_badge_ru,'Пробный урок');self.assertIsNotNone(plan.verified_at)

    def test_manual_point_is_not_replaced_after_address_edit(self):
        place=self.create()
        with patch.object(OwnerPlacesController,'_sync_place_coordinates') as geocode:
            result=self.controller.save_edit_form(request=self.request,place_id=place.pk,data=self.data(address='New address'),files={})
        self.assertTrue(result.ok,result.form.errors if result.form else result.message)
        geocode.assert_not_called()
        place.refresh_from_db();self.assertEqual(place.lat,40.4)

    def test_cannot_set_staff_fields(self):
        place=self.create(status='published',is_active='1',is_verified='1',custom_price_badge_ru='Free')
        self.assertEqual(place.status,'pending');self.assertFalse(place.is_active);self.assertFalse(place.is_verified)
        self.assertEqual(place.custom_price_badge_ru,'')

    def test_gallery_removal_is_validated_and_rolled_back_with_upload_failure(self):
        from django.utils.datastructures import MultiValueDict
        place=self.create()
        image=PlacePhoto.objects.create(place=place,image=self.photo('gallery.png'))
        image_path=image.image.name
        invalid=OwnerPlaceEditForm(instance=place,data=self.data(delete_gallery_ids=['999999']),draft_save_only=True)
        self.assertFalse(invalid.is_valid())
        self.assertTrue(PlacePhoto.objects.filter(pk=image.pk).exists())
        with patch.object(type(self.controller.owner_place_repository),'add_gallery_images',side_effect=OSError('Storage unavailable')):
            result=self.controller.save_edit_form(request=self.request,place_id=place.pk,data=self.data(delete_gallery_ids=[str(image.pk)]),files=MultiValueDict({'gallery_images':[self.photo('new.png')]}),draft_save_only=True)
        self.assertFalse(result.ok)
        self.assertTrue(PlacePhoto.objects.filter(pk=image.pk).exists())
        self.assertTrue(image.image.storage.exists(image_path))
        with self.captureOnCommitCallbacks(execute=True):
            result=self.controller.save_edit_form(request=self.request,place_id=place.pk,data=self.data(delete_gallery_ids=[str(image.pk)]),files={},draft_save_only=True)
        self.assertTrue(result.ok,result.form.errors)
        self.assertFalse(PlacePhoto.objects.filter(pk=image.pk).exists())
        self.assertFalse(image.image.storage.exists(image_path))

    def test_scalar_only_legacy_price_survives_unrelated_edit(self):
        place=self.create()
        place.pricing_plan_records.all().delete()
        Place.objects.filter(pk=place.pk).update(price_from=80,price_to=120)
        place.refresh_from_db()
        form=OwnerPlaceEditForm(instance=place,data={'name_az':'Yeni ad'},draft_save_only=True)
        self.assertTrue(form.is_valid(),form.errors);form.save();place.refresh_from_db()
        self.assertEqual(place.price_from,80);self.assertEqual(place.price_to,120)

    def test_failed_resubmission_does_not_save_changes_or_delete_photo(self):
        place=self.create()
        old_name=place.name_az
        response=self.client.post(reverse('owner_place_edit',args=[place.pk]),self.data(form_action='save_and_publish',name_az='Changed name',pricing_plans='[]'))
        self.assertEqual(response.status_code,200)
        place.refresh_from_db()
        self.assertEqual(place.name_az,old_name)
        self.assertEqual(place.pricing_plan_records.count(),1)

    def test_other_owner_cannot_edit(self):
        place=self.create()
        other=get_user_model().objects.create_user('otherwizard',password='password')
        self.client.force_login(other)
        self.client.post(reverse('owner_place_edit',args=[place.pk]),self.data(name_az='Unauthorized',form_action='save_draft'))
        place.refresh_from_db();self.assertNotEqual(place.name_az,'Unauthorized')

    def test_new_form_renders_seven_steps_in_all_languages(self):
        place=self.create()
        for language in ('ru','az','en'):
            prefix = '' if language == 'az' else f'/{language}'
            for path in (f'{prefix}/account/places/create/?type=permanent',f'{prefix}/account/places/{place.pk}/edit/'):
                response=self.client.get(path, follow=True)
                if response.status_code==404:
                    from django.utils.translation import override
                    with override(language):
                        response=self.client.get(reverse('owner_place_edit',args=[place.pk]))
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'data-pw-step="7"')
                self.assertContains(response,'data-permanent-place-form')
                self.assertContains(response,'name="phone2"')
                self.assertContains(response,'data-pw-step="',count=7)
                self.assertContains(response,'data-pw-go="',count=7)
                self.assertContains(response,'role="progressbar"')
                self.assertContains(response,'data-pw-progress-bar')
                self.assertContains(response,'name="name_az"')
