"""Regression boundaries for moderation preview, redirects and stale decisions."""
from unittest.mock import patch
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext, override
from catalog.models import Place, PlaceOwnershipRequest
from catalog.proxy_apps.catalog_moderation.models import ModerationPlace
from catalog.testcases import test_ownership_admin_preview as fixtures


class AdminPlaceModerationFixTests(TestCase):
    def setUp(self):
        fixtures.OwnershipAdminPreviewTests.setUp(self)
        self.preview_url = f'/admin/catalog/place/{self.place.pk}/site-preview/'
        self.owner_admin = admin.site._registry[PlaceOwnershipRequest]

    def stale(self):
        self.item.base_ownership_version = self.place.ownership_version + 1
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_ownership_version=self.item.base_ownership_version)

    def test_pending_place_has_a_private_read_only_preview_without_a_request(self):
        self.item.delete()
        before = (self.place.status, self.place.content_version, self.place.is_active)
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
            response = self.client.get(self.preview_url)
            self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Полная карточка RU')
        self.assertContains(response, 'Превью на сайте')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('noindex', response['X-Robots-Tag'])
        self.place.refresh_from_db()
        self.assertEqual(before, (self.place.status, self.place.content_version, self.place.is_active))
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(self.preview_url).status_code, 405)

    def test_pending_place_media_link_is_private(self):
        response = self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{self.preview_url}"')
        # The old media action promised public content that could only return 404.
        self.assertNotContains(response, f'href="{self.place.get_absolute_url()}" target="_blank" rel="noopener">Посмотреть на сайте')

    def test_unpublished_place_list_actions_use_private_preview(self):
        for model in (Place, ModerationPlace):
            model_admin = admin.site._registry[model]
            for status, active in ((Place.STATUS_PENDING, True), (Place.STATUS_DRAFT, True),
                                   (Place.STATUS_PUBLISHED, False), (Place.STATUS_PUBLISHED, True)):
                self.place.status, self.place.is_active = status, active
                expected = self.place.get_absolute_url() if self.place.is_public else self.preview_url
                for method in ('col_actions', 'row_actions'):
                    with self.subTest(model=model.__name__, status=status, active=active, method=method):
                        html = str(getattr(model_admin, method)(self.place))
                        self.assertIn(f'href="{expected}"', html)
                        if not self.place.is_public:
                            self.assertNotIn(f'href="{self.place.get_absolute_url()}"', html)
                            self.assertNotIn(f'data-view-url="{self.place.get_absolute_url()}"', html)

    def test_private_preview_checks_permission_and_never_leaks_staff_session(self):
        staff = get_user_model().objects.create_user('preview_no_permissions', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.preview_url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.preview_url).status_code, 302)
        self.client.force_login(self.staff)
        for lang in ('az', 'ru', 'en'):
            response = self.client.get(self.preview_url, {'lang': lang, 'next': '//untrusted.invalid/'})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['request'].user.is_authenticated)
            self.assertEqual(response['Content-Language'], lang)
            self.assertEqual(response.context['site_preview_back'], reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertEqual(self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk])).status_code, 200)

    def test_proxy_publish_redirects_to_concrete_place(self):
        model_admin = admin.site._registry[ModerationPlace]
        request = RequestFactory().post('/admin/catalog_moderation/moderationplace/')
        request.user = self.staff
        with patch.object(model_admin, 'message_user') as message:
            response = model_admin._handle_publish_submit(request, self.place)
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'published')
        self.assertEqual(response.url, reverse('admin:catalog_place_change', args=[self.place.pk]))
        message.assert_called()
        self.assertEqual(self.client.get(response.url).status_code, 200)
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 200)

    def test_stale_list_actions_explain_block_and_do_not_offer_accept(self):
        self.stale()
        for method in ('col_actions', 'row_actions'):
            html = str(getattr(self.owner_admin, method)(self.item))
            self.assertNotIn('/approve/', html)
            self.assertIn('Заявка устарела', html)
            self.assertIn('/reject/', html)

    def test_stale_confirmation_has_reason_without_submit_and_post_remains_rejected(self):
        self.stale()
        url = reverse('admin:catalog_placeownershiprequest_approve', args=[self.item.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заявка устарела')
        self.assertTrue(response.context['approval_blocked'])
        self.assertNotContains(response, 'class="km-inspection-confirm-actions"')
        self.client.post(url)
        self.item.refresh_from_db()
        self.place.refresh_from_db()
        self.assertEqual(self.item.status, 'PENDING')
        self.assertFalse(self.place.is_public)

    def test_stale_request_change_form_does_not_offer_approval(self):
        self.stale()
        url = reverse('admin:catalog_placeownershiprequest_change', args=[self.item.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заявка устарела')
        self.assertNotIn('km-btn--success-alt', response.content.decode())

    def test_current_request_can_still_open_confirmation(self):
        url = reverse('admin:catalog_placeownershiprequest_approve', args=[self.item.pk])
        self.assertContains(self.client.get(url), 'class="km-inspection-confirm-actions"')

    def test_ru_moderation_labels_mean_the_actions_they_name(self):
        with override('ru'):
            for label in ('Открыть', 'Низкая оценка', 'Риски'):
                self.assertEqual(gettext(label), label)

    def test_az_en_moderation_labels_are_not_unrelated_history_or_empty_states(self):
        expected = {
            'az': {'Низкая оценка': 'Aşağı qiymət', 'Предпросмотр': 'Ön baxış',
                   'Карточка опубликована — уже видна на сайте': 'Kart dərc olunub — artıq saytda görünür'},
            'en': {'Низкая оценка': 'Low rating', 'Предпросмотр': 'Preview',
                   'Карточка опубликована — уже видна на сайте': 'Listing published — now visible on the site'},
        }
        for language, labels in expected.items():
            with override(language):
                for source, translated in labels.items():
                    self.assertEqual(gettext(source), translated)
