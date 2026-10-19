"""Regressions from the explicitly approved F01-F12 local repair plan."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image


class CategoryUploadPermissionTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        setting = override_settings(MEDIA_ROOT=self.media.name)
        setting.enable()
        self.addCleanup(setting.disable)
        self.staff = get_user_model().objects.create_user(
            username='repair_category_staff', is_staff=True)
        self.url = reverse('admin:catalog_category_upload_icon')
        self.client.force_login(self.staff)

    @staticmethod
    def icon():
        image = BytesIO()
        Image.new('RGB', (512, 512), '#136f38').save(image, format='PNG')
        return SimpleUploadedFile('fictional-icon.png', image.getvalue(), content_type='image/png')

    def test_staff_without_category_permission_cannot_write_icon(self):
        self.assertFalse(self.staff.has_perm('catalog.change_category'))
        response = self.client.post(self.url, {'file': self.icon(), 'code': 'fictional-denied'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual([p for p in Path(self.media.name).rglob('*') if p.is_file()], [])

    def test_category_editor_can_upload_valid_icon(self):
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='change_category'))
        response = self.client.post(self.url, {'file': self.icon(), 'code': 'fictional-allowed'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len([p for p in Path(self.media.name).rglob('*') if p.is_file()]), 1)

    def test_upload_still_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertEqual(client.post(self.url, {'file': self.icon()}).status_code, 403)

    def test_anonymous_cannot_write_icon(self):
        self.client.logout()
        response = self.client.post(self.url, {'file': self.icon()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual([p for p in Path(self.media.name).rglob('*') if p.is_file()], [])

    def test_volunteer_cannot_use_upload_even_with_accidental_model_permission(self):
        from django.contrib.auth.models import Group
        from catalog.services.staff_roles import VOLUNTEER_GROUP
        group, _ = Group.objects.get_or_create(name=VOLUNTEER_GROUP)
        self.staff.groups.add(group)
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='change_category'))
        self.assertEqual(self.client.post(self.url, {'file': self.icon()}).status_code, 403)
        self.assertEqual([p for p in Path(self.media.name).rglob('*') if p.is_file()], [])

    def test_wrong_method_remains_405_for_permitted_editor(self):
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='change_category'))
        self.assertEqual(self.client.get(self.url).status_code, 405)


class CategorySvgValidationTests(SimpleTestCase):
    @staticmethod
    def icon(body='', *, viewbox='0 0 24 24', prefix=''):
        data=(prefix+'<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+viewbox+'">'+body+'</svg>').encode()
        return SimpleUploadedFile('fictional.svg', data, content_type='image/svg+xml')

    def validate(self, upload):
        from catalog.domain_admin.category import validate_icon_upload
        return validate_icon_upload(upload)

    def test_standard_shapes_gradients_and_local_shape_reference_remain_supported(self):
        source=self.icon('<defs><linearGradient id="paint"><stop offset="0" stop-color="#136f38"/>'
            '<stop offset="100%" stop-color="white"/></linearGradient>'
            '<path id="shape" d="M 1 1 L 20 1 L 20 20 Z"/></defs>'
            '<g transform="translate(1 0)"><rect width="20" height="20" fill="url(#paint)"/>'
            '<use href="#shape" fill="currentColor"/></g>')
        validated=self.validate(source)
        self.assertIn(b'linearGradient', validated.read())
        validated.seek(0)
        self.assertIn(b'url(#paint)', validated.read())

    def test_processing_instructions_are_not_stored(self):
        # An inert processing instruction verifies canonical serialization.
        result=self.validate(self.icon('<path d="M0 0 L1 1"/>',prefix='<?xml-stylesheet?>')).read()
        self.assertNotIn(b'xml-stylesheet', result)

    def test_non_icon_elements_are_rejected(self):
        from django.core.exceptions import ValidationError
        for body in ['<foreignObject/>','<animate/>','<style/>','<a/>',
                     '<image href="https://example.invalid/fictional.png"/>',
                     '<use id="cycle" href="#cycle"/>']:
            with self.subTest(body=body),self.assertRaises(ValidationError):
                self.validate(self.icon(body))

    def test_unsupported_event_attributes_are_rejected_even_when_empty(self):
        from django.core.exceptions import ValidationError
        for name in ['onfocus','onclick','onpointerenter']:
            with self.subTest(name=name),self.assertRaises(ValidationError):
                self.validate(self.icon(f'<path d="M0 0 L1 1" {name}=""/>'))

    def test_external_and_unknown_paint_references_are_rejected(self):
        from django.core.exceptions import ValidationError
        for value in ['url(https://example.invalid/paint.svg#x)','url(#missing)',
                      'url(data:fictional)','inherit;other:value']:
            with self.subTest(value=value),self.assertRaises(ValidationError):
                self.validate(self.icon(f'<rect width="20" height="20" fill="{value}"/>'))

    def test_safe_inline_presentation_is_converted_to_validated_attributes(self):
        from xml.etree import ElementTree
        result=self.validate(self.icon('<path d="M0 0 L1 1" style="fill:#136f38;stroke-width:2"/>')).read()
        path=list(ElementTree.fromstring(result))[0]
        self.assertNotIn('style', path.attrib)
        self.assertEqual(path.attrib['fill'], '#136f38')
        self.assertEqual(path.attrib['stroke-width'], '2')

    def test_non_finite_or_invalid_viewbox_is_rejected(self):
        from django.core.exceptions import ValidationError
        for box in ['0 0 inf inf','0 0 0 0','0 0 24 12','0 0 -1 -1']:
            with self.subTest(box=box),self.assertRaises(ValidationError):
                self.validate(self.icon(viewbox=box))

    def test_document_type_and_foreign_namespace_are_rejected(self):
        from django.core.exceptions import ValidationError
        for upload in [self.icon(prefix='<!DOCTYPE svg>'),
                       self.icon('<foreign:path xmlns:foreign="urn:fictional:foreign"/>')]:
            with self.subTest(upload=upload.name),self.assertRaises(ValidationError):
                self.validate(upload)

    def test_svg_tree_depth_and_element_count_are_bounded(self):
        from django.core.exceptions import ValidationError
        for body in ['<g>'*40+'</g>'*40, '<path/>'*3000]:
            with self.subTest(length=len(body)),self.assertRaises(ValidationError):
                self.validate(self.icon(body))

    def test_storage_uses_validated_canonical_svg(self):
        from catalog.domain_admin.category import save_uploaded_category_icon
        with TemporaryDirectory() as media,override_settings(MEDIA_ROOT=media):
            save_uploaded_category_icon(self.icon('<path style="fill:#136f38"/>',prefix='<?xml-stylesheet?>'))
            saved=list(Path(media).rglob('*.svg'))
            self.assertEqual(len(saved),1)
            data=saved[0].read_bytes()
            self.assertNotIn(b'xml-stylesheet',data)
            self.assertNotIn(b'style=',data)


class ProgramConflictRecoveryTests(TestCase):
    def setUp(self):
        from catalog.models import Organization
        self.owner=get_user_model().objects.create_user(username='repair_program_owner')
        self.org=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='Fictional network')
        self.client.force_login(self.owner)

    def program(self, suffix=''):
        from catalog.models import Program
        return Program.objects.create(organization=self.org,created_by=self.owner,name_az='Original '+suffix)

    @staticmethod
    def payload(name, program, revision=0):
        return {'name_az':name,'name_ru':'','name_en':'',
            'description_az':'','description_ru':'','description_en':'',
            'expected_version':program.content_version,'revision_version':revision,'submit':'1'}

    def url(self, program, lang='ru'):
        from django.utils.translation import override
        with override(lang):
            return reverse('organization_program_save',args=[self.org.pk,program.pk])

    @staticmethod
    def retry_payload(response):
        form=response.context['form']
        return {**{name:form[name].value() or '' for name in form.fields},'submit':'1'}

    def test_conflict_preserves_input_shows_current_and_refreshes_tokens_in_all_languages(self):
        for lang in ['az','ru','en']:
            with self.subTest(lang=lang):
                program=self.program(lang)
                url=self.url(program,lang)
                first=self.client.post(url,self.payload('First saved '+lang,program),HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(first.status_code,302)
                response=self.client.post(url,self.payload('Second retained '+lang,program),HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(response.status_code,409)
                program.refresh_from_db()
                current=program.content_revision
                self.assertEqual(response.context['form']['name_az'].value(),'Second retained '+lang)
                self.assertEqual(int(response.context['form']['revision_version'].value()),current.version)
                self.assertEqual(int(response.context['form']['expected_version'].value()),program.content_version)
                self.assertEqual(current.payload['name_az'],'First saved '+lang)
                self.assertEqual(program.name_az,'Original '+lang)
                self.assertContains(response,'data-program-conflict',status_code=409)
                self.assertContains(response,'data-program-current',status_code=409)
                self.assertContains(response,'First saved '+lang,status_code=409)
                self.assertNotContains(response,'Candidate version conflict.',status_code=409)
                retry=self.client.post(url,self.retry_payload(response),HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(retry.status_code,302)
                program.refresh_from_db()
                self.assertEqual(program.content_revision.payload['name_az'],'Second retained '+lang)
                self.assertEqual(program.name_az,'Original '+lang)

    def test_a_further_concurrent_edit_still_requires_another_explicit_retry(self):
        program=self.program()
        url=self.url(program)
        self.client.post(url,self.payload('First saved',program))
        conflict=self.client.post(url,self.payload('Second retained',program))
        retry=self.retry_payload(conflict)
        program.refresh_from_db()
        self.client.post(url,self.payload('Third saved',program,program.content_revision.version))
        latest=self.client.post(url,retry)
        self.assertEqual(latest.status_code,409)
        program.refresh_from_db()
        self.assertEqual(program.content_revision.payload['name_az'],'Third saved')
        self.assertEqual(latest.context['form']['name_az'].value(),'Second retained')
        self.assertEqual(int(latest.context['form']['revision_version'].value()),program.content_revision.version)

    def test_invalid_fields_keep_validation_errors_without_recovery_retry_state(self):
        program=self.program()
        invalid=self.client.post(self.url(program),self.payload('',program))
        self.assertEqual(invalid.status_code,400)
        self.assertIn('name_az',invalid.context['form'].errors)
        self.assertNotContains(invalid,'data-program-conflict',status_code=400)

    def test_program_permissions_are_checked_again_on_an_explicit_retry(self):
        program=self.program()
        url=self.url(program)
        self.client.post(url,self.payload('First saved',program))
        conflict=self.client.post(url,self.payload('Second retained',program))
        outsider=get_user_model().objects.create_user(username='repair_program_outsider')
        self.client.force_login(outsider)
        self.assertEqual(self.client.post(url,self.retry_payload(conflict)).status_code,404)
        program.refresh_from_db()
        self.assertEqual(program.content_revision.payload['name_az'],'First saved')
