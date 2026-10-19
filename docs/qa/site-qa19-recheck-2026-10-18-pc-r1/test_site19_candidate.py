"""SITE19 contract tests. Run against unchanged application; no model monkeypatches."""
import json
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import gettext, override
from catalog.models import CatalogContentSettings
from catalog.models.site import clear_singleton_caches

FIELDS = ('districts_json', 'metro_stations_json', 'seo_pages_json')
INITIAL = {'districts_json': ['baku', {'key': 'qa', 'districts': ['qa_child']}],
           'metro_stations_json': ['QA метро', 'QA stansiya'],
           'seo_pages_json': {'ru': {'qa': {'title': 'QA «текст»'}},
                              'az': {'qa': {'title': 'QA mətn'}},
                              'en': {'qa': {'title': 'QA text'}}}}

class Site19StringContract(SimpleTestCase):
    def assert_label(self, obj):
        try:
            result = str(obj)
        except TypeError as exc:
            self.fail(str(exc))
        self.assertIsInstance(result, str)
        self.assertEqual(result, gettext('Контент каталога'))
        return result

    def test_unsaved_real_string_in_all_locales_without_queries(self):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang), override(lang):
                self.assert_label(CatalogContentSettings())

    def test_same_object_uses_active_language_each_call(self):
        obj = CatalogContentSettings(pk=17)
        for lang in ('en', 'ru', 'az', 'en'):
            with self.subTest(lang=lang), override(lang):
                self.assert_label(obj)

class Site19AdminContract(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.obj = CatalogContentSettings.get_solo()
        for key, value in INITIAL.items():
            setattr(cls.obj, key, value)
        cls.obj.save()
        User = get_user_model()
        cls.superuser = User.objects.create_superuser('site19_test_super', 'site19_super@example.invalid', 'fictional')
        cls.editor = User.objects.create_user('site19_test_editor', 'site19_editor@example.invalid', 'fictional', is_staff=True)
        cls.viewer = User.objects.create_user('site19_test_viewer', 'site19_viewer@example.invalid', 'fictional', is_staff=True)
        cls.denied = User.objects.create_user('site19_test_denied', 'site19_denied@example.invalid', 'fictional', is_staff=True)
        for user, codes in [(cls.editor, ['view_catalogcontentsettings', 'change_catalogcontentsettings']),
                            (cls.viewer, ['view_catalogcontentsettings'])]:
            user.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog', codename__in=codes))

    def setUp(self):
        cache.clear()
        clear_singleton_caches()
        self.client = Client(raise_request_exception=False)
        self.url = reverse('admin:catalog_catalogcontentsettings_change', args=[self.obj.pk])

    def login_language(self, user, lang):
        self.client.force_login(user)
        self.client.cookies['django_language'] = lang

    def snapshot(self):
        return (CatalogContentSettings.objects.values(*FIELDS, 'updated_at').get(pk=self.obj.pk), LogEntry.objects.count())

    def payload(self, values=None):
        return {key: json.dumps((values or INITIAL)[key], ensure_ascii=False) for key in FIELDS}

    def test_persisted_model_string_is_read_only(self):
        before = self.snapshot()
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang), override(lang):
                obj = CatalogContentSettings.objects.get(pk=self.obj.pk)
                with self.assertNumQueries(0):
                    try:
                        label = str(obj)
                    except TypeError as exc:
                        self.fail(str(exc))
                    self.assertEqual(label, gettext('Контент каталога'))
        self.assertEqual(self.snapshot(), before)

    def test_authorized_editor_get_renders_json_fields_without_write(self):
        for user in (self.superuser, self.editor):
            for lang in ('az', 'ru', 'en'):
                with self.subTest(role=user.username, lang=lang):
                    self.login_language(user, lang)
                    before = self.snapshot()
                    response = self.client.get(self.url)
                    self.assertEqual(response.status_code, 200)
                    self.assertTemplateUsed(response, 'admin/catalog/shared_settings_change_form.html')
                    for key in FIELDS:
                        self.assertContains(response, 'name="' + key + '"')
                    self.assertEqual(self.snapshot(), before)

    def test_view_only_get_is_read_only(self):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang):
                self.login_language(self.viewer, lang)
                before = self.snapshot()
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                for key in FIELDS:
                    self.assertNotContains(response, 'name="' + key + '"')
                self.assertEqual(self.snapshot(), before)

    def test_valid_json_roundtrip_and_admin_log(self):
        for user in (self.superuser, self.editor):
            for lang in ('az', 'ru', 'en'):
                with self.subTest(role=user.username, lang=lang):
                    self.login_language(user, lang)
                    values = json.loads(json.dumps(INITIAL))
                    values['metro_stations_json'] += [lang + '-' + user.username + '-roundtrip']
                    before_count = LogEntry.objects.count()
                    response = self.client.post(self.url, {**self.payload(values), '_continue': '1'})
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(CatalogContentSettings.objects.values(*FIELDS).get(pk=self.obj.pk), values)
                    self.assertEqual(LogEntry.objects.count(), before_count + 1)
                    entry = LogEntry.objects.latest('pk')
                    with override(lang):
                        self.assertEqual(entry.object_repr, gettext('Контент каталога'))

    def test_invalid_json_returns_bound_form_and_preserves_storage(self):
        self.login_language(self.editor, 'en')
        for key in FIELDS:
            with self.subTest(field=key):
                before = self.snapshot()
                data = self.payload(); data[key] = '{broken-json'
                response = self.client.post(self.url, {**data, '_continue': '1'})
                self.assertEqual(response.status_code, 200)
                self.assertIn(key, response.context['adminform'].form.errors)
                self.assertEqual(response.context['adminform'].form[key].value(), '{broken-json')
                self.assertEqual(self.snapshot(), before)

    def test_viewer_and_denied_posts_cannot_write(self):
        for user in (self.viewer, self.denied):
            with self.subTest(user=user.username):
                self.login_language(user, 'ru'); before = self.snapshot()
                response = self.client.post(self.url, self.payload())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(self.snapshot(), before)

    def test_denied_get_is_forbidden(self):
        self.login_language(self.denied, 'az'); before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_anonymous_is_redirected_to_login(self):
        before = self.snapshot(); response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])
        self.assertEqual(self.snapshot(), before)

    def test_singleton_add_delete_and_index_stay_disabled(self):
        self.login_language(self.superuser, 'ru'); before = self.snapshot()
        for action in ('add', 'delete'):
            url = reverse('admin:catalog_catalogcontentsettings_' + action,
                          args=[self.obj.pk] if action == 'delete' else [])
            self.assertEqual(self.client.get(url).status_code, 403)
        request = RequestFactory().get('/admin/'); request.user = self.superuser
        self.assertEqual(admin.site._registry[CatalogContentSettings].get_model_perms(request), {})
        self.assertEqual(self.snapshot(), before)

    def test_existing_content_methods_keep_json_semantics(self):
        obj = CatalogContentSettings.objects.get(pk=self.obj.pk)
        before = self.snapshot()
        self.assertEqual(obj.districts(), ['baku', 'qa', 'qa_child'])
        self.assertEqual(obj.metro_stations(), INITIAL['metro_stations_json'])
        for lang in ('az', 'ru', 'en'):
            self.assertEqual(obj.seo_pages(lang), INITIAL['seo_pages_json'][lang])
        self.assertEqual(self.snapshot(), before)
