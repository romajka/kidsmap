"""The website preview renders public components without publishing a Place."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection, transaction
from django.test import TestCase
from catalog.models import PlaceOwnershipRequest, VolunteerPlaceRevision, FunnelEvent, PlaceChangeAudit
from catalog.services import publication
from catalog.testcases import test_ownership_admin_preview as fixtures


class OwnershipSitePreviewTests(TestCase):
    def setUp(self):
        fixtures.OwnershipAdminPreviewTests.setUp(self)
        self.site_url = self.url.replace('/preview/', '/site-preview/')

    def candidate(self, **payload):
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=publication.snapshot(self.place, 'place'),
            dependencies=publication.dependencies(self.place, 'place'),
            schema_version=publication.SCHEMA_VERSION, changed_fields=list(payload),
            payload=payload, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=1)
        return revision

    def test_preview_uses_the_real_public_page_for_an_unpublished_place(self):
        response = self.client.get(self.site_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/place_detail.html')
        self.assertContains(response, 'css/pages/detail.css')
        self.assertContains(response, 'Полная карточка RU')
        self.assertContains(response, 'Full description EN', count=0)
        self.assertContains(response, 'Полное описание RU')
        self.assertContains(response, 'Превью на сайте')
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 404)

    def test_site_preview_is_read_only_private_and_not_indexable(self):
        before = (FunnelEvent.objects.count(), PlaceChangeAudit.objects.count(), self.place.content_version)
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor: cursor.execute('SET TRANSACTION READ ONLY')
            response = self.client.get(self.site_url)
            self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(before, (FunnelEvent.objects.count(), PlaceChangeAudit.objects.count(), self.place.content_version))
        self.assertFalse(self.place.is_public)
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertIn('noindex', response.headers['X-Robots-Tag'])
        self.assertContains(response, 'content="noindex,nofollow"')
        self.assertNotContains(response, 'googletagmanager.com')
        self.assertEqual(self.client.post(self.site_url).status_code, 405)

    def test_submitted_price_and_schedule_are_used_without_changing_live(self):
        base = publication.snapshot(self.place, 'place')
        schedule = base['structured_schedule']
        schedule[0]['is_closed'] = False
        schedule[0]['intervals'] = [{'start':'10:30', 'end':'14:15'}]
        plans = base['pricing_plans']
        plans[0].update(price='28.00', is_active=True)
        self.candidate(description_ru='Отправленный текст для сайта', structured_schedule=schedule, pricing_plans=plans)
        response = self.client.get(self.site_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отправленный текст для сайта')
        self.assertContains(response, '10:30')
        self.assertContains(response, '14:15')
        self.assertEqual(response.context['pricing_summary']['amount'], 28)
        self.place.refresh_from_db()
        self.assertNotEqual(self.place.description_ru, 'Отправленный текст для сайта')
        current = self.client.get(self.site_url+'?version=current')
        self.assertNotContains(current, 'Отправленный текст для сайта')

    def test_languages_and_guest_appearance_preserve_staff_session(self):
        for lang, name in [('ru','Полная карточка RU'), ('en','Full card EN')]:
            response = self.client.get(self.site_url, {'lang':lang})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['language'], lang)
            self.assertFalse(response.context['request'].user.is_authenticated)
            self.assertContains(response, name)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_anonymous_owner_and_staff_without_place_permission_cannot_preview(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.site_url).status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.site_url).status_code, 302)
        staff = get_user_model().objects.create_user('site_preview_limited', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_placeownershiprequest'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.site_url).status_code, 403)

    def test_inspection_has_a_website_preview_link_with_current_version_and_return(self):
        response = self.client.get(self.url, {'version':'current', 'next':'/admin/catalog/placeownershiprequest/?status__exact=PENDING'})
        self.assertContains(response, 'Превью на сайте')
        link = response.context['preview_site_url']
        self.assertIn('/site-preview/', link)
        self.assertIn('version=current', link)
        preview = self.client.get(link)
        self.assertEqual(preview.status_code, 200)
        self.assertIn('version=current', preview.context['site_preview_back'])

    def test_live_published_preview_matches_public_presentation(self):
        self.place.status='published'; self.place.is_active=True
        self.place.save(update_fields=['status','is_active'])
        live = self.client.get(self.place.get_absolute_url())
        self.assertEqual(live.status_code, 200)
        preview = self.client.get(self.site_url)
        self.assertEqual(preview.status_code, 200)
        for key in ['name','description','prices','contacts']:
            self.assertEqual(preview.context['presentation'][key], live.context['presentation'][key])
        self.assertEqual(preview.context['pricing_summary'], live.context['pricing_summary'])

    def test_published_group_candidate_uses_sent_teacher_and_price(self):
        self.activity.status='published';self.activity.save(update_fields=['status'])
        tree=publication.snapshot(self.place,'place')['nested_pricing']
        group=tree['activities'][0]['groups'][0]
        group['teachers_text']='Преподаватель отправленной версии'
        group['pricing_plans'][0]['price']='49.00'
        self.candidate(nested_pricing=tree)
        response=self.client.get(self.site_url)
        self.assertEqual(response.status_code,200)
        presentation=response.context['activities'][0]['groups'][0]
        self.assertEqual(presentation['teachers'],'Преподаватель отправленной версии')
        self.assertIn('49',presentation['prices'][0]['label'])
        self.assertEqual(response.context['activities'][0]['url'],'')
        self.group.refresh_from_db()
        self.assertNotEqual(self.group.teachers_text,'Преподаватель отправленной версии')

    def test_new_submitted_activity_is_rendered_but_explicit_empty_tree_is_not_live(self):
        tree=publication.snapshot(self.place,'place')['nested_pricing']
        tree['activities'][0]['id']=None
        tree['activities'][0]['name_ru']='Новое направление из заявки'
        tree['activities'][0]['groups'][0]['id']=None
        tree['activities'][0]['groups'][0]['pricing_plans'][0]['id']=None
        revision=self.candidate(nested_pricing=tree)
        response=self.client.get(self.site_url)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Новое направление из заявки')
        self.assertEqual(len(response.context['activities']),1)
        revision.payload={'nested_pricing':{'pricing_schema_version':2,'activities':[]}}
        revision.save(update_fields=['payload'])
        self.assertEqual(self.client.get(self.site_url).context['activities'],[])

    def test_unsent_draft_activities_are_not_presented_as_published(self):
        response=self.client.get(self.site_url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['activities'],[])

    def test_removed_submitted_tariffs_do_not_resurrect_old_scalar_prices(self):
        self.candidate(pricing_plans=[])
        response=self.client.get(self.site_url)
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.context['pricing_summary']['has_price'])
        self.assertIsNone(response.context['place'].price_from)
