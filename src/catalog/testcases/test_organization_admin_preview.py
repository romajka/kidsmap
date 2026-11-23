from django.contrib.auth.models import Permission
from django.core.files.storage import default_storage
from django.urls import reverse

from catalog.models import Organization, VolunteerPlaceRevision
from catalog.testcases.test_organization_lifecycle_v2 import OrganizationV2Base, image_upload


class OrganizationAdminPreviewTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        self.org.owner = self.staff
        self.org.name_ru = 'Сохранённое название'
        self.org.address = 'Audit Avenue'
        self.org.save(update_fields=['owner', 'name_ru', 'address'])
        self.client.force_login(self.staff)
        self.client.cookies['django_language'] = 'ru'
        self.url = f'/admin/catalog/organization/{self.org.pk}/site-preview/'

    def test_saved_draft_renders_public_template_with_private_headers(self):
        self.propose({'name_ru': 'Название из черновика'}, submit=False, actor=self.staff)
        page = self.client.get(self.url, {'lang': 'ru'})
        self.assertTemplateUsed(page, 'catalog/public_entity_detail.html')
        self.assertContains(page, 'Название из черновика')
        self.assertNotContains(page, 'public-org-fact--verified')
        self.assertEqual(page['Content-Language'], 'ru')
        self.assertIn('no-store', page['Cache-Control'])
        self.assertIn('noindex', page['X-Robots-Tag'])
        self.assertEqual(self.client.get(self.url, {'lang': 'en'})['Content-Language'], 'en')
        self.assertEqual(self.client.get(f'/ru/organizations/{self.org.public_id}/').status_code, 404)

    def test_form_edits_and_unsaved_upload_show_without_persistence(self):
        page = self.client.post(self.url, {
            'preview_language': 'en', 'source_version': self.org.content_version,
            'candidate_version': 0, 'name_az': 'Yeni ad', 'name_en': 'Unsaved organization',
            'description_en': 'Unsaved description', 'logo': image_upload(),
            '_save_and_publish': '1',
        })
        self.assertContains(page, 'Unsaved organization')
        self.assertContains(page, 'Unsaved description')
        self.assertContains(page, 'data:image/png;base64,')
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az, 'Günəş Akademiyası')
        self.assertFalse(self.org.logo)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())
        self.assertFalse(default_storage.exists('organizations'))

    def test_preview_permissions_match_view_and_change_permissions(self):
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), f'/admin/login/?next={self.url}', fetch_redirect_response=False)
        self.stranger.is_staff = True
        self.stranger.save(update_fields=['is_staff'])
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.stranger.user_permissions.add(Permission.objects.get(codename='view_organization'))
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)
        listing = self.client.get(reverse('admin:catalog_organization_changelist'))
        self.assertContains(listing, self.url)
        self.assertNotContains(listing, '>Редактировать</a>')

    def test_admin_search_matches_address_and_owner(self):
        listing = reverse('admin:catalog_organization_changelist')
        for query in ('Audit Avenue', self.staff.username):
            with self.subTest(query=query):
                page = self.client.get(listing, {'q': query})
                self.assertContains(page, f'/admin/catalog/organization/{self.org.pk}/change/')
                suggestion = self.client.get(reverse('admin:catalog_organization_search_suggestions'), {'q': query})
                self.assertEqual([row['id'] for row in suggestion.json()['results']], [self.org.pk])

    def test_new_organization_can_be_previewed_before_first_save(self):
        before = Organization.objects.count()
        page = self.client.post('/admin/catalog/organization/site-preview/', {
            'preview_language': 'az', 'source_version': 0, 'candidate_version': 0,
            'name_az': 'Yeni təşkilat',
        })
        self.assertContains(page, 'Yeni təşkilat')
        self.assertEqual(Organization.objects.count(), before)


class OrganizationAdminEditorTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        self.org.owner = self.staff
        self.org.save(update_fields=['owner'])
        self.client.force_login(self.staff)
        self.client.cookies['django_language'] = 'ru'
        self.add = reverse('admin:catalog_organization_add')
        self.change = reverse('admin:catalog_organization_change', args=[self.org.pk])

    def test_add_and_edit_share_required_fields_and_optional_sections(self):
        for url in (self.add, self.change):
            with self.subTest(url=url):
                page = self.client.get(url)
                self.assertContains(page, 'data-org-editor-section="profile"')
                self.assertContains(page, 'data-org-editor-section="media"')
                self.assertContains(page, 'aria-required="true"', count=1)
                form = page.context['adminform'].form
                required = {name for name, field in form.fields.items() if field.required}
                self.assertEqual(required, {'name_az'})

    def test_invalid_optional_field_is_visible_and_does_not_create_organization(self):
        before = Organization.objects.count()
        page = self.client.post(self.add, {
            'source_version': 0, 'candidate_version': 0, 'name_az': 'Yeni təşkilat',
            'website': 'garbage://x', '_save_draft': '1',
        })
        self.assertFormError(page.context['adminform'].form, 'website', 'Введите правильный URL.')
        self.assertContains(page, 'data-org-editor-section="contacts" open')
        self.assertContains(page, 'href="#id_website"')
        self.assertEqual(Organization.objects.count(), before)

    def test_minimal_public_card_falls_back_to_az_and_omits_empty_optional_values(self):
        page = self.client.post(self.add, {
            'source_version': 0, 'candidate_version': 0, 'name_az': 'Sadə təşkilat',
            '_save_and_publish': '1',
        })
        self.assertEqual(page.status_code, 302)
        org = Organization.objects.get(name_az='Sadə təşkilat')
        self.assertTrue(org.is_public)
        for language in ('az', 'ru', 'en'):
            url = f'/{language}/organizations/{org.slug}/' if language != 'az' else f'/organizations/{org.slug}/'
            with self.subTest(language=language):
                public = self.client.get(url)
                self.assertContains(public, '<h1 class="public-org-title" lang="az">Sadə təşkilat</h1>', html=True)
                self.assertNotContains(public, 'id="org-description"')
                self.assertNotContains(public, 'public-org-actions-bar')
                self.assertNotContains(public, 'orgv-mbar__main')

    def test_saved_draft_stays_in_editor_with_outcome(self):
        page = self.client.post(self.add, {
            'source_version': 0, 'candidate_version': 0, 'name_az': 'Qaralama təşkilat',
            '_save_draft': '1',
        }, follow=True)
        org = Organization.objects.get(name_az='Qaralama təşkilat')
        self.assertFalse(org.is_public)
        self.assertEqual(page.request['PATH_INFO'], reverse('admin:catalog_organization_change', args=[org.pk]))
        self.assertContains(page, 'Черновик сохранён.')

    def test_same_number_sets_public_whatsapp_and_ignores_separate_input(self):
        page = self.client.post(self.add, {
            'source_version': 0, 'candidate_version': 0, 'name_az': 'Əlaqəli təşkilat',
            'phone': '050 555 12 34', 'whatsapp': 'old incomplete number',
            'whatsapp_same_as_phone': 'on', '_save_and_publish': '1',
        })
        self.assertEqual(page.status_code, 302)
        org = Organization.objects.get(name_az='Əlaqəli təşkilat')
        self.assertEqual(org.phone, '+994505551234')
        self.assertEqual(org.whatsapp, org.phone)
        public = self.client.get(f'/ru/organizations/{org.slug}/')
        self.assertContains(public, 'href="https://wa.me/994505551234"')
        self.assertNotContains(public, 'class="orgv-mbar__main" href="#branches"')
