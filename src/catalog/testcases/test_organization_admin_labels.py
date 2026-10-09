"""ORG-10: labels follow the UI language after forms were imported once."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.domain_admin.business import OrganizationForm
from catalog.models import Organization

LABELS = {
    'ru': ('Название организации', 'Описание организации'),
    'az': ('Təşkilatın adı', 'Təşkilatın təsviri'),
    'en': ('Organization name', 'Organization description'),
}


class OrganizationLabelLanguageTests(SimpleTestCase):
    def test_reused_form_follows_language_switch_after_import(self):
        form = OrganizationForm()
        for language in ('ru', 'az', 'en', 'ru'):
            with override(language):
                for kind, title in zip(('name', 'description'), LABELS[language]):
                    for data_language in ('az', 'ru', 'en'):
                        with self.subTest(language=language, field=f'{kind}_{data_language}'):
                            label = form[f'{kind}_{data_language}'].label
                            self.assertEqual(str(label), f'{title} ({data_language.upper()})')


class OrganizationAdminLabelRequestTests(TestCase):
    def test_add_and_change_in_one_process_follow_each_request_language(self):
        staff = get_user_model().objects.create_superuser(
            username='org10_staff', email='org10-staff@example.invalid', password='synthetic')
        org = Organization.objects.create(owner=staff, created_by=staff, name_az='ORG10 Synthetic network')
        self.client.force_login(staff)
        urls = (reverse('admin:catalog_organization_add'),
                reverse('admin:catalog_organization_change', args=[org.pk]))
        for language in ('en', 'ru', 'az', 'en'):
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
            for url in urls:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                form = response.context['adminform'].form
                for kind, title in zip(('name', 'description'), LABELS[language]):
                    for data_language in ('az', 'ru', 'en'):
                        expected = f'{title} ({data_language.upper()})'
                        with self.subTest(language=language, url=url, field=f'{kind}_{data_language}'):
                            self.assertEqual(str(form[f'{kind}_{data_language}'].label), expected)
                            self.assertContains(response, expected)
