"""Current editor POST preview is private, read-only and uses the public template."""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services import publication, publication_forms
from catalog.testcases.test_content_entry_final import CandidateMediaFixture

class PlaceEditorPreviewTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp();self.place.refresh_from_db();self.client.force_login(self.owner)
        self.url=reverse('place_editor_preview',kwargs={'pk':self.place.pk})
    def payload(self,**changes):
        return {'publication_token':publication_forms.version_token(self.place),'name_az':'Cari məkan',
            'description_az':'Preview from the current editor.',**changes}
    def test_empty_check_reports_each_missing_field_once_without_repeating_the_publication_summary(self):
        for user,suffix in ((self.owner,''),(self.staff,'?surface=admin')):
            with self.subTest(surface=suffix):
                self.client.force_login(user)
                response=self.client.post(reverse('place_editor_preview_new')+suffix,{'_km_check_required':'1'})
                self.assertEqual(response.status_code,422)
                errors=response.json()['errors']
                self.assertEqual(len(errors['name_az']),1)
                self.assertNotIn('__all__',errors)
                self.assertIn('description_az',errors)
    def test_current_unsaved_text_uses_public_template_without_sql_writes(self):
        before=publication.snapshot(self.place,'place')
        with CaptureQueriesContext(connection) as queries:
            response=self.client.post(self.url,self.payload())
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,'catalog/place_detail.html')
        self.assertContains(response,'Cari məkan')
        self.assertContains(response,'Preview from the current editor.')
        writes=[q['sql'] for q in queries if q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE'))]
        self.assertEqual(writes,[])
        self.place.refresh_from_db();self.assertEqual(before,publication.snapshot(self.place,'place'))
        self.assertEqual(VolunteerPlaceRevision.objects.filter(place=self.place).count(),0)
        self.assertIn('no-store',response.headers['Cache-Control']);self.assertIn('noindex',response.headers['X-Robots-Tag'])
    def test_foreign_owner_and_anonymous_cannot_preview(self):
        self.client.force_login(self.other);self.assertEqual(self.client.post(self.url,self.payload()).status_code,403)
        self.client.logout();self.assertIn(self.client.post(self.url,self.payload()).status_code,(302,403))
    def test_preview_requires_post_and_csrf(self):
        self.assertEqual(self.client.get(self.url).status_code,405)
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.post(self.url,self.payload()).status_code,403)
    def test_invalid_letters_in_phone_are_rejected_with_field_error(self):
        response=self.client.post(self.url,self.payload(phone1='+99450abc1234567'))
        self.assertEqual(response.status_code,422);self.assertContains(response,'phone1',status_code=422)
    def test_new_place_can_be_previewed_without_creating_a_listing(self):
        before=Place.objects.count()
        response=self.client.post(reverse('place_editor_preview_new'),{'name_az':'Yeni məkan','description_az':'An unsaved place.','whatsapp_mode':'none'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'Yeni məkan')
        self.assertEqual(Place.objects.count(),before)

    def test_new_preview_does_not_query_relations_using_its_temporary_url_id(self):
        with CaptureQueriesContext(connection) as queries:
            response=self.client.post(reverse('place_editor_preview_new'),{'name_az':'Yeni məkan','description_az':'An unsaved place.','whatsapp_mode':'none'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(any(str(10**9) in query['sql'] for query in queries),'A transient URL ID must never read another listing’s reviews, events or practices')
    def test_uploaded_photo_is_rendered_without_persistent_media(self):
        from pathlib import Path
        from django.conf import settings
        before={str(path.relative_to(settings.MEDIA_ROOT)) for path in Path(settings.MEDIA_ROOT).rglob('*') if path.is_file()}
        response=self.client.post(self.url,self.payload(photo=SimpleUploadedFile('preview.png',self.image(),content_type='image/png')))
        self.assertEqual(response.status_code,200);self.assertContains(response,'data:image/')
        self.place.refresh_from_db();self.assertFalse(self.place.photo)
        self.assertEqual(before,{str(path.relative_to(settings.MEDIA_ROOT)) for path in Path(settings.MEDIA_ROOT).rglob('*') if path.is_file()})
    def test_bad_tariff_range_is_a_field_error_and_xss_is_escaped(self):
        plans=self.place.pricing_plans;plans[0].update(price_kind='range',price=None,price_min='100',price_max='1')
        response=self.client.post(self.url,self.payload(pricing_plans=json.dumps(plans)))
        self.assertEqual(response.status_code,422)
        response=self.client.post(self.url,self.payload(name_az='<script>alert(1)</script>'))
        self.assertEqual(response.status_code,200);self.assertNotContains(response,'<script>alert(1)</script>')

    def test_admin_current_form_preview_is_read_only_and_invalid_gallery_is_422(self):
        from catalog.testcases import admin as existing_admin_tests
        self.client.force_login(self.staff)
        data=existing_admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update(name_az='Admin cari məkan',pricing_plans=json.dumps(self.place.pricing_plans))
        url=self.url+'?surface=admin'
        response=self.client.post(url,data)
        self.assertEqual(response.status_code,200);self.assertContains(response,'Admin cari məkan')
        self.place.refresh_from_db();self.assertNotEqual(self.place.name_az,'Admin cari məkan')
        data['gallery_uploads']=SimpleUploadedFile('broken.png',b'not an image',content_type='image/png')
        response=self.client.post(url,data)
        self.assertEqual(response.status_code,422)

    def test_long_text_and_international_letters_keep_their_actual_content(self):
        text=('Ə ə İ ı Ş ş Ç ç Ö ö Ü ü Привет Hello 🙂\n'*70).strip()
        response=self.client.post(self.url,self.payload(description_az=text))
        self.assertEqual(response.status_code,200);self.assertContains(response,'Ə ə İ ı Ş ş')
        self.assertContains(response,'Привет Hello 🙂')

    def test_invalid_phone_matrix_has_no_preview_or_storage_side_effects(self):
        before=publication.snapshot(self.place,'place')
        for value in ['abc','+99450O1234567','+99450<script>','++994501234567','994+501234567','+994501234567,+994551234567','123','+999123456789','+994'+'1'*30]:
            with self.subTest(value=value):
                response=self.client.post(self.url,self.payload(phone1=value))
                self.assertEqual(response.status_code,422)
                self.assertContains(response,'phone1',status_code=422)
        self.place.refresh_from_db();self.assertEqual(before,publication.snapshot(self.place,'place'))

    def test_text_and_numeric_boundaries_use_the_same_server_form_rules(self):
        limit=Place._meta.get_field('name_az').max_length
        for value,expected in [('A'*limit,200),('A'*(limit+1),422),('Ə'*limit,200)]:
            with self.subTest(length=len(value)):
                self.assertEqual(self.client.post(self.url,self.payload(name_az=value)).status_code,expected)
        for changes in [{'age_from':'12','age_to':'3'},{'age_from':'-1'},{'category':'missing-category'},{'website':'javascript:alert(1)'},{'lat':'200','lng':'50'}]:
            with self.subTest(changes=changes):self.assertEqual(self.client.post(self.url,self.payload(**changes)).status_code,422)

    def test_invalid_money_values_are_rejected_without_losing_stored_plans(self):
        for value in ['-1','NaN','Infinity','999999999999999999999999999']:
            plans=self.place.pricing_plans;plans[0].update(price_kind='exact',price=value,price_min=None,price_max=None)
            with self.subTest(value=value):self.assertEqual(self.client.post(self.url,self.payload(pricing_plans=json.dumps(plans))).status_code,422)

    def test_check_completeness_returns_field_errors_without_submitting(self):
        before=publication.snapshot(self.place,'place')
        response=self.client.post(self.url,self.payload(_km_check_required='1',name_az='',description_az=''))
        self.assertEqual(response.status_code,422)
        payload=response.json();self.assertFalse(payload['ok']);self.assertIn('name_az',payload['errors'])
        self.place.refresh_from_db();self.assertEqual(before,publication.snapshot(self.place,'place'))
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_missing_legacy_photo_does_not_crash_preview(self):
        Place.objects.filter(pk=self.place.pk).update(photo='places/fictional-missing-file.webp')
        self.place.refresh_from_db()
        self.assertEqual(self.client.post(self.url,self.payload()).status_code,200)

    def test_admin_inline_gallery_upload_is_included_as_a_distinct_preview_image(self):
        import re
        from catalog.testcases import admin as existing_admin_tests
        self.client.force_login(self.staff)
        data=existing_admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update({'gallery-TOTAL_FORMS':'1','gallery-INITIAL_FORMS':'0','gallery-MAX_NUM_FORMS':'10',
            'gallery-0-image':SimpleUploadedFile('gallery.png',self.image('blue'),content_type='image/png'),
            'gallery-0-order':'0','photo':SimpleUploadedFile('main.png',self.image('green'),content_type='image/png')})
        response=self.client.post(self.url+'?surface=admin',data)
        self.assertEqual(response.status_code,200)
        urls=set(re.findall(r'data:image/[^"\s<]+',response.content.decode()))
        self.assertGreaterEqual(len(urls),2)
        self.assertEqual(self.place.gallery.count(),0)

    def test_completeness_price_errors_include_the_server_field_address(self):
        plans=self.place.pricing_plans;plans[0].update(price_kind='range',price=None,price_min='100',price_max='1')
        response=self.client.post(self.url,self.payload(_km_check_required='1',pricing_plans=json.dumps(plans)))
        self.assertEqual(response.status_code,422)
        path=response.json()['error_targets']['pricing_plans'][0]
        self.assertEqual(path[:2],['pricing_plans',0]);self.assertIn(path[2],['price_min','price_max'])

    def test_preview_applies_the_existing_total_upload_budget(self):
        from unittest.mock import patch
        from catalog.testcases import admin as existing_admin_tests
        for surface in ('owner','admin'):
            with self.subTest(surface=surface):
                self.client.force_login(self.owner if surface=='owner' else self.staff)
                data=self.payload() if surface=='owner' else existing_admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
                data['photo']=SimpleUploadedFile('main.png',self.image(),content_type='image/png')
                with patch('catalog.services.image_uploads.MAX_IMAGE_BATCH_BYTES',1):
                    response=self.client.post(self.url+('?surface=admin' if surface=='admin' else ''),data)
                self.assertEqual(response.status_code,422)

    def test_admin_failed_save_exposes_the_tariff_error_binding(self):
        import re
        from catalog.testcases import admin as existing_admin_tests
        self.client.force_login(self.staff)
        data=existing_admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        plans=self.place.pricing_plans;plans[0].update(price_kind='range',price=None,price_min='100',price_max='1')
        data.update(pricing_plans=json.dumps(plans),_save_draft='1')
        response=self.client.post(reverse('admin:catalog_place_change',args=[self.place.pk]),data)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'data-pf-field="pricing_plans"')
        payload=re.search(r'id="km-editor-error-targets"[^>]*>(.*?)</script>',response.content.decode(),re.S)
        self.assertIsNotNone(payload)
        self.assertEqual(json.loads(payload[1])['pricing_plans'][0],['pricing_plans',0,'price_max'])
        errors=re.search(r'id="km-editor-errors"[^>]*>(.*?)</script>',response.content.decode(),re.S)
        self.assertIsNotNone(errors);self.assertIn('pricing_plans',json.loads(errors[1]))

    def test_legacy_published_edit_permission_is_not_a_false_completeness_result(self):
        from catalog.testcases import admin as existing_admin_tests
        Place.objects.filter(pk=self.place.pk).update(status='published',is_active=True,description_az='')
        self.place.refresh_from_db();self.client.force_login(self.staff)
        data=existing_admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update(description_az='',_km_check_required='1')
        response=self.client.post(self.url+'?surface=admin',data)
        self.assertEqual(response.status_code,422)
        self.assertIn('description_az',response.json()['errors'])
        self.place.refresh_from_db();self.assertEqual(self.place.status,'published');self.assertEqual(self.place.description_az,'')
