import json
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from catalog.testcases.test_content_entry_final import CandidateMediaFixture
from catalog.testcases.test_task33_publication import PublicationFixture


class PublicLinkValidationTests(SimpleTestCase):
    def test_private_drafts_keep_partial_links_while_public_validation_rejects_them(self):
        from catalog.services.server_drafts import _fields
        from catalog.services.place_public_links import normalize_public_links
        partial=[{'label':'Запись','url':'https://'}]
        self.assertEqual(_fields('place',{'public_links':partial}),{'public_links':partial})
        self.assertEqual(_fields('place',{'public_links':[]}),{'public_links':[]})
        with self.assertRaises(ValidationError):normalize_public_links(partial)

    def test_supports_named_public_pages_and_rejects_executable_or_credential_urls(self):
        from catalog.services.place_public_links import normalize_public_links
        self.assertEqual(normalize_public_links([{'label':'  Запись  ','url':'https://example.com/book?q=1'}]),[{'label':'Запись','url':'https://example.com/book?q=1'}])
        for value in ([{'label':'X','url':'javascript:alert(1)'}],[{'label':'X','url':'https://user:pass@example.com'}],{'url':'https://example.com'},[{'label':'','url':'https://example.com'}],[{'label':'X','url':'https://example.com','extra':True}],[{'label':'X','url':'https://example.com'}]*6):
            with self.subTest(value=value),self.assertRaises(ValidationError):normalize_public_links(value)


class PublicLinkFlowTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp();self.client.force_login(self.owner)

    def test_rendered_owner_fields_include_examples_and_keep_phone_guidance(self):
        response=self.client.get('/ru/account/places/create/?type=permanent&fresh=1')
        self.assertEqual(response.status_code,200)
        for text in ('Правила посещения:','Полезные детали:','Имя профиля или ссылка:','Официальный сайт места.','050 123 45 67'):
            self.assertContains(response,text)

    def test_owner_feedback_keeps_all_contact_fields_and_uses_configured_google_provider(self):
        from django.test import override_settings
        for configured in (False,True):
            with self.subTest(configured=configured),override_settings(GOOGLE_MAPS_API_KEY='synthetic-browser-key' if configured else ''):
                response=self.client.get('/ru/account/places/create/?type=permanent&fresh=1')
                self.assertEqual(response.status_code,200)
                for name in ('phone1','phone2','phone3','whatsapp_mode','whatsapp_number','instagram','website','public_links'):
                    self.assertContains(response,f'name="{name}"',count=1)
                self.assertContains(response,'data-km-phone-slot',count=2)
                self.assertContains(response,'data-km-phone-add',count=1)
                self.assertContains(response,'Рекомендуется')
                self.assertContains(response,'Зачем добавлять другие языки?')
                self.assertContains(response,'data-tariff-heading')
                self.assertContains(response,'data-map-provider="google"' if configured else 'data-map-provider="unavailable"')
                self.assertNotContains(response,'unpkg.com/leaflet')

    def test_admin_json_export_retains_public_links_for_future_edits(self):
        links=[{'label':'Запись','url':'https://example.com/book'}]
        self.place.public_links=links;self.place.save(update_fields=['public_links'])
        self.client.force_login(self.staff)
        response=self.client.get(reverse('admin:catalog_place_export_json',args=[self.place.pk]))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['public_links'],links)

    def test_link_preview_is_private_and_omitted_links_survive_existing_edits(self):
        from catalog.services import publication,publication_forms
        links=[{'label':'Запись на урок','url':'https://example.com/book'}]
        self.place.public_links=links;self.place.save(update_fields=['public_links'])
        data={'publication_token':publication_forms.version_token(self.place),'name_az':'Bakı məkan','description_az':'Public link preview test.'}
        response=self.client.post(reverse('place_editor_preview',kwargs={'pk':self.place.pk}),data)
        self.assertEqual(response.status_code,200,response.context['form'].errors if response.context and 'form' in response.context else response.content[:800]);self.assertContains(response,'https://example.com/book');self.assertContains(response,'Запись на урок')
        self.assertEqual(publication.snapshot(self.place,'place')['public_links'],links)
        proposed=[{'label':'Новая страница','url':'https://example.com/new'}]
        response=self.client.post(reverse('place_editor_preview',kwargs={'pk':self.place.pk}),{**data,'public_links':json.dumps(proposed)})
        self.assertEqual(response.status_code,200);self.assertContains(response,'https://example.com/new')
        self.place.refresh_from_db();self.assertEqual(self.place.public_links,links)
        response=self.client.post(reverse('place_editor_preview',kwargs={'pk':self.place.pk}),{**data,'public_links':'[{"label":"X","url":"javascript:alert(1)"}]'})
        self.assertEqual(response.status_code,422)


class PublicLinkModerationTests(PublicationFixture,TestCase):
    def test_pending_and_rejected_links_do_not_leak_and_approval_updates_same_place(self):
        links=[{'label':'Запись','url':'https://example.com/book'}]
        revision=self.propose({'public_links':links})
        self.place.refresh_from_db();self.assertEqual(self.place.public_links,[])
        self.s.review(actor=self.staff,revision_id=revision.pk,version=revision.version,approve=False,note='Проверьте ссылку')
        self.place.refresh_from_db();self.assertEqual(self.place.public_links,[])
        revision.refresh_from_db();revision=self.propose({'public_links':links},revision_version=revision.version)
        self.approve(revision);self.place.refresh_from_db();self.assertEqual(self.place.public_links,links)

    def test_hostile_direct_publication_patch_is_rejected(self):
        with self.assertRaises(ValidationError):self.propose({'public_links':[{'label':'X','url':'javascript:alert(1)'}]})
