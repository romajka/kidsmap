"""Visible server validation, accessible error targets and rejected-input retention."""
from html.parser import HTMLParser
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Organization

class FormDOM(HTMLParser):
    def __init__(self, html):
        super().__init__();self.ids={};self.inputs={};self.links=[];self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids[attrs['id']]=(tag,attrs)
        if tag in ('input','textarea') and attrs.get('name'):self.inputs[attrs['name']]=attrs
        if tag=='a':self.links.append(attrs)

class OrganizationEditorErrorTests(TestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='org05_owner')
        self.other=get_user_model().objects.create_user(username='org05_other')
        self.org=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='Synthetic ORG05 live name')
        self.client=Client(enforce_csrf_checks=True);self.client.force_login(self.owner)
        token=get_token(RequestFactory().get('/'));self.client.cookies['csrftoken']=token;self.client.defaults['HTTP_X_CSRFTOKEN']=token
        self.data={'name_az':'Synthetic ORG05 candidate','name_ru':'Synthetic RU','name_en':'Synthetic EN','phone':'+994 00 000 00 00','whatsapp':'+994 00 000 00 01','website':'https://example.invalid/','description_az':'Synthetic description','expected_version':self.org.content_version,'revision_version':0,'submit':'1'}
    def save(self, **values):
        return self.client.post(reverse('organization_workspace_save',args=[self.org.pk]),{**self.data,**values})
    def unchanged(self):
        self.org.refresh_from_db();self.assertEqual(self.org.name_az,'Synthetic ORG05 live name');self.assertFalse(hasattr(self.org,'content_revision'))
    def test_each_rejected_field_has_visible_error_and_accessible_target_in_all_languages(self):
        bad={'name_ru':'R'*256,'name_en':'E'*256,'phone':'P'*51,'whatsapp':'W'*51,'website':'invalid URL'}
        for lang in ('ru','az','en'):
            with self.subTest(lang=lang),override(lang):
                response=self.save(**bad);self.assertEqual(response.status_code,400);dom=FormDOM(response.content.decode())
                self.assertIn('org-editor-errors',dom.ids)
                form=response.context['candidate_form'];self.assertTrue(form.is_bound)
                for name in bad:
                    field=form[name];attrs=dom.inputs[name]
                    self.assertEqual(attrs['value'],bad[name]);self.assertEqual(attrs.get('aria-invalid'),'true')
                    refs=attrs.get('aria-describedby','').split();self.assertTrue(refs,name)
                    for ref in refs:self.assertIn(ref,dom.ids,name)
                    for error in field.errors:self.assertContains(response,str(error),status_code=400)
                    self.assertTrue(any(a.get('href')=='#'+field.id_for_label and 'data-org-error-target' in a for a in dom.links),name)
                self.assertContains(response,'data-org-server-errors',status_code=response.status_code);self.unchanged()
    def test_hidden_version_errors_are_visible_in_summary(self):
        response=self.save(expected_version='bad',revision_version='bad')
        self.assertEqual(response.status_code,400);dom=FormDOM(response.content.decode());self.assertIn('org-editor-errors',dom.ids)
        for name in ('expected_version','revision_version'):
            for error in response.context['candidate_form'][name].errors:self.assertContains(response,str(error),status_code=400)
        self.assertFalse(any(a.get('href') in ('#id_expected_version','#id_revision_version') for a in dom.links));self.unchanged()
    def test_nonfield_version_error_gets_summary_without_losing_values(self):
        response=self.save(expected_version=0)
        self.assertEqual(response.status_code,409);self.assertTrue(response.context['candidate_form'].non_field_errors())
        self.assertContains(response,'id="org-editor-errors"',status_code=409);self.assertContains(response,'data-org-server-errors',status_code=response.status_code)
        self.assertEqual(response.context['candidate_form']['name_ru'].value(),self.data['name_ru']);self.unchanged()
    def test_correct_and_repeat_invalid_input_do_not_change_live_or_publish(self):
        for _ in range(2):
            response=self.save(phone='P'*51);self.assertEqual(response.status_code,400);self.assertContains(response,'org-editor-errors',status_code=response.status_code);self.unchanged()
        response=self.save();self.assertEqual(response.status_code,302)
        self.org.refresh_from_db();self.assertEqual(self.org.name_az,'Synthetic ORG05 live name');self.assertEqual(self.org.content_revision.payload['phone'],self.data['phone']);self.assertEqual(self.org.content_revision.status,'pending')
    def test_conflict_keeps_winning_candidate_and_returns_losing_input_in_summary(self):
        self.assertEqual(self.save().status_code,302)
        response=self.save(name_az='Synthetic losing candidate')
        self.assertEqual(response.status_code,409);self.assertContains(response,'org-editor-errors',status_code=response.status_code)
        self.assertEqual(response.context['candidate_form']['name_az'].value(),'Synthetic losing candidate')
        self.org.refresh_from_db();self.assertEqual(self.org.content_revision.payload['name_az'],self.data['name_az'])
    def test_foreign_actor_and_csrf_are_still_denied_without_private_form(self):
        self.client.force_login(self.other);response=self.save(phone='P'*51);self.assertEqual(response.status_code,404);self.assertNotContains(response,'Synthetic ORG05 live name',status_code=404)
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        response=client.post(reverse('organization_workspace_save',args=[self.org.pk]),self.data);self.assertEqual(response.status_code,403);self.unchanged()
