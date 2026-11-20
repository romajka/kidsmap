from html.parser import HTMLParser
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone

from catalog.models import SiteSettings, Specialist
from catalog.services.specialist_proposal_drafts import save_proposal


class QualificationEditorTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user('qualification-editor')
        self.client.force_login(self.actor)
        settings = SiteSettings.get_solo()
        settings.specialists_section_enabled = True
        settings.save()

    def test_own_application_has_optional_private_file_controls_in_each_language(self):
        for prefix, title in (('', 'Diplomlar və sertifikatlar'), ('/ru', 'Дипломы и сертификаты'),
                              ('/en', 'Diplomas and certificates')):
            with self.subTest(prefix=prefix):
                page = self.client.get(f'{prefix}/account/places/specialists/create/', follow=True)
                self.assertEqual(page.status_code, 200)
                self.assertContains(page, 'data-qualification-editor')
                self.assertContains(page, title)
                inputs = {}

                class InputParser(HTMLParser):
                    def handle_starttag(self, tag, attrs):
                        attrs = dict(attrs)
                        if tag == 'input' and 'name' in attrs:
                            inputs[attrs['name']] = attrs

                InputParser().feed(page.content.decode())
                self.assertEqual(inputs['qual-0-file']['type'], 'file')
                self.assertNotIn('required', inputs['qual-0-file'])
                self.assertNotIn('checked', inputs['qual-0-publish'])
                self.assertEqual(inputs['qual-INITIAL_FORMS']['value'], '0')
                self.assertContains(page, 'name="qual-0-type"')
                self.assertContains(page, 'name="qual-0-name"')

    def test_upload_precedes_limits_and_each_consent_explains_publication(self):
        page = self.client.get('/ru/account/places/specialists/create/', follow=True)
        section = page.content.decode().split('id="km-sec-documents"', 1)[1].split('</section>', 1)[0]
        self.assertLess(section.index('id="km-qual-picker"'), section.index('id="km-qual-file-hint"'))
        consent = section.split('for="id_qual-0-publish"', 1)[1].split('</label>', 1)[0]
        self.assertIn('после подтверждения профиля и проверки документа', consent)

    def test_third_party_draft_cannot_render_qualification_inputs(self):
        values = QueryDict('', mutable=True)
        values.update({'profile_subject': 'other', 'locations-TOTAL_FORMS': '0',
                       'locations-INITIAL_FORMS': '0', 'locations-MIN_NUM_FORMS': '0', 'locations-MAX_NUM_FORMS': '30'})
        draft = save_proposal(actor=self.actor, draft_id=uuid4(), expected_version='0', data=values, files={})
        page = self.client.get(f'/ru/account/specialists/proposals/{draft.pk}/')
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'data-qualification-editor')
        self.assertNotContains(page, 'name="qual-0-file"')

    def test_confirmed_editor_links_to_qualification_management(self):
        profile = Specialist.objects.create(name='Confirmed teacher', verified_person_user=self.actor,
                                            person_verified_at=timezone.now())
        page = self.client.get(f'/ru/account/specialists/{profile.pk}/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, f'data-qualification-manage href="/ru/account/specialists/{profile.pk}/certificates/"')
