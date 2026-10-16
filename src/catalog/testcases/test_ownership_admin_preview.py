"""Staff can inspect an unpublished request without publishing or tracking it."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.conf import settings
from django.db import connection, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import (Place, PlaceOwnershipRequest, PlacePhoto, Activity,
    OfferingGroup, PricingPlan, VolunteerPlaceRevision, PlaceChangeAudit,
    PlaceOwnershipRequestAudit, FunnelEvent)
from catalog.services import publication
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.testcases.utils import create_ready_place


class OwnershipAdminPreviewTests(TestCase):
    def setUp(self):
        language = override('ru')
        language.__enter__()
        self.addCleanup(language.__exit__, None, None, None)
        users = get_user_model()
        self.staff = users.objects.create_superuser('preview_staff', 'preview@example.invalid', 'fictional')
        self.owner = users.objects.create_user('preview_owner')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner,
            name_ru='Полная карточка RU', name_en='Full card EN',
            description_ru='Полное описание RU ' * 25, description_en='Full description EN',
            status='pending', is_active=False, phone2='+994502223344', phone3='+994503334455',
            extra_conditions_ru='Все условия RU', additional_info_en='Additional EN',
            schedule_note_ru='Примечание расписания RU')
        PlacePhoto.objects.create(place=self.place, image='places/gallery/fictional.jpg', caption='Полная подпись фото')
        self.activity = Activity.objects.create(place=self.place, category=self.place.category,
            name_az='Rəsm', name_ru='Рисование', description_en='Activity EN', status='draft')
        self.group = OfferingGroup.objects.create(activity=self.activity, name_ru='Группа 6–10 лет',
            language='AZ / RU', schedule_text='Вт 16:00–18:00', teachers_text='Преподаватель фикстуры')
        PricingPlan.objects.create(offering_group=self.group, product_type='lesson', price='35',
            title_ru='Групповой тариф', conditions_en='Group conditions EN')
        PricingPlan.objects.create(place=self.place, product_type='lesson', price='9',
            title_ru='Неактивный тариф', is_active=False)
        self.item = PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner,
            request_kind=PlaceOwnershipRequest.KIND_PUBLICATION, note='Проверьте всю карточку')
        self.url = reverse('admin:catalog_placeownershiprequest_change', args=[self.item.pk]).replace('/change/', '/preview/')
        self.client.force_login(self.staff)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'

    def test_unpublished_full_card_is_available_inside_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/catalog/placeownershiprequest/preview.html')
        for value in ['Полная карточка RU', 'Full card EN', 'Full description EN',
                      '+994502223344', '+994503334455', 'Все условия RU', 'Additional EN',
                      'Примечание расписания RU', 'Полная подпись фото', 'Рисование',
                      'Группа 6–10 лет', 'Преподаватель фикстуры', 'Групповой тариф',
                      'Group conditions EN', 'Неактивный тариф', '09:00–18:00']:
            self.assertContains(response, value)
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 404)

    def test_list_preview_link_does_not_use_the_public_page(self):
        from django.contrib import admin
        html = admin.site._registry[PlaceOwnershipRequest].col_actions(self.item)
        self.assertIn(self.url, str(html))
        self.assertIn('Проверить карточку', str(html))

    def test_get_is_read_only_even_in_a_postgres_read_only_transaction(self):
        before = (self.place.content_version, self.place.status, self.place.is_active,
            PlaceChangeAudit.objects.count(), PlaceOwnershipRequestAudit.objects.count(), FunnelEvent.objects.count())
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
                    cursor.execute('SHOW transaction_read_only')
                    self.assertEqual(cursor.fetchone()[0], 'on')
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db(); self.item.refresh_from_db()
        after = (self.place.content_version, self.place.status, self.place.is_active,
            PlaceChangeAudit.objects.count(), PlaceOwnershipRequestAudit.objects.count(), FunnelEvent.objects.count())
        self.assertEqual(before, after)
        self.assertEqual(self.item.status, 'PENDING')
        self.assertIn('no-store', response.headers.get('Cache-Control', ''))

    def test_preview_post_cannot_publish_or_edit(self):
        self.assertEqual(self.client.post(self.url, {'action':'approve','name_ru':'Spoof'}).status_code, 405)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, 'Полная карточка RU')
        self.assertFalse(self.place.is_active)

    def test_pending_candidate_and_all_unchanged_sections_are_shown(self):
        base = publication.snapshot(self.place, 'place')
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=base, base_content_version=self.place.content_version,
            payload={'description_ru':'Предложенное описание RU'}, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=revision.version)
        response = self.client.get(self.url)
        self.assertContains(response, 'Предложенное описание RU')
        self.assertContains(response, 'Group conditions EN')
        self.assertContains(response, 'Полная подпись фото')
        self.place.refresh_from_db(); revision.refresh_from_db()
        self.assertNotEqual(self.place.description_ru, 'Предложенное описание RU')
        self.assertEqual(revision.payload, {'description_ru':'Предложенное описание RU'})

    def test_explicit_empty_candidate_tree_is_not_replaced_by_live_groups(self):
        base = publication.snapshot(self.place, 'place')
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=base, payload={'nested_pricing':{'pricing_schema_version':2,'activities':[]}},
            status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Группа 6–10 лет')
        self.assertTrue(OfferingGroup.objects.filter(pk=self.group.pk).exists())

    def test_stale_publication_request_is_flagged_without_approve_action(self):
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_content_version=0)
        response = self.client.get(self.url)
        self.assertContains(response, 'Заявка устарела')
        self.assertFalse(response.context['preview_can_approve'])

    def test_claim_does_not_display_an_unsubmitted_content_draft(self):
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            payload={'description_ru':'Несохранённая для проверки версия'}, status='draft')
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(request_kind='CLAIM')
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Несохранённая для проверки версия')
        self.assertContains(response, 'Полное описание RU')
        self.assertContains(response, 'Подтвердить владение')

    def test_object_and_model_permissions_are_required(self):
        staff = get_user_model().objects.create_user('limited_preview', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_placeownershiprequest'))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_place'))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['preview_can_moderate'])

    def test_owner_and_volunteer_cannot_inspect_staff_data(self):
        self.client.force_login(self.owner)
        self.assertIn(self.client.get(self.url).status_code, (302,403))
        volunteer = get_user_model().objects.create_user('preview_volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        volunteer.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog', codename__in=['view_place','view_placeownershiprequest']))
        self.client.force_login(volunteer)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_untrusted_text_and_external_links_are_not_executable(self):
        Place.objects.filter(pk=self.place.pk).update(description_ru='<script>preview_xss()</script>', website='javascript:preview_xss()')
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;preview_xss()&lt;/script&gt;')
        self.assertNotContains(response, 'href="javascript:preview_xss()"')

    def test_processed_request_keeps_content_but_no_decision_buttons(self):
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(status='APPROVED')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Полная карточка RU')
        self.assertFalse(response.context['preview_can_approve'])
        self.assertFalse(response.context['preview_can_moderate'])

    def test_deleted_applicant_and_empty_card_are_renderable(self):
        empty = Place.objects.create(name='Пустая карточка', category=self.place.category, status='draft', is_active=False)
        item = PlaceOwnershipRequest.objects.create(place=empty, applicant=None)
        response = self.client.get(reverse('admin:catalog_placeownershiprequest_preview', args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Фотографии не добавлены')
        self.assertFalse(response.context['preview_can_approve'])

    def test_current_version_cannot_approve_a_different_submitted_candidate(self):
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=publication.snapshot(self.place, 'place'),
            payload={'description_ru':'На проверке'}, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=revision.version)
        response = self.client.get(self.url+'?version=current')
        self.assertContains(response, 'Полное описание RU')
        self.assertFalse(response.context['preview_can_approve'])
        self.assertContains(response, 'Перейти к проверке')

    def test_return_url_is_local_and_missing_request_is_404(self):
        response = self.client.get(self.url, {'next':'//attacker.invalid/'})
        self.assertEqual(response.context['preview_back_url'], reverse('admin:catalog_placeownershiprequest_changelist'))
        self.assertEqual(self.client.get(self.url.replace(str(self.item.pk), '99999999')).status_code, 404)

    def test_changed_submitted_group_source_is_flagged_before_approval(self):
        import copy
        base = publication.snapshot(self.place, 'place')
        candidate = copy.deepcopy(base['nested_pricing'])
        candidate['activities'][0]['groups'][0]['conditions_ru'] = 'Отправленные условия группы'
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=base,
            dependencies=publication.dependencies(self.place, 'place'),
            changed_fields=['nested_pricing'], payload={'nested_pricing':candidate}, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=revision.version)
        OfferingGroup.objects.filter(pk=self.group.pk).update(schedule_text='Новое расписание после отправки')
        response = self.client.get(self.url)
        self.assertTrue(response.context['preview']['stale'])
        self.assertFalse(response.context['preview_can_approve'])

    def test_ownership_moderator_without_publication_permission_cannot_publish(self):
        staff = get_user_model().objects.create_user('claims_only', is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',
            codename__in=['view_place','change_placeownershiprequest']))
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['preview_can_approve'])
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(request_kind='CLAIM')
        response = self.client.get(self.url)
        self.assertTrue(response.context['preview_can_approve'])

    def test_request_form_remains_usable_and_links_back_to_full_preview(self):
        response = self.client.get(reverse('admin:catalog_placeownershiprequest_change', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url)
        self.assertContains(response, self.place.description_ru.strip())

    def test_candidate_without_required_review_dependencies_is_not_approvable(self):
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=publication.snapshot(self.place, 'place'),
            payload={'description_ru':'Старая заявка'}, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=1)
        response = self.client.get(self.url)
        self.assertTrue(response.context['preview']['stale'])
        self.assertFalse(response.context['preview_can_approve'])

    def test_preview_decision_link_confirms_and_publishes_the_inspected_candidate(self):
        proposed = 'Полное предложенное описание для публикации. ' * 20
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            base_snapshot=publication.snapshot(self.place, 'place'),
            dependencies=publication.dependencies(self.place, 'place'),
            schema_version=publication.SCHEMA_VERSION, changed_fields=['description_ru'],
            base_content_version=self.place.content_version,
            payload={'description_ru':proposed}, status='pending', version=1)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_candidate_version=1)
        response = self.client.get(self.url)
        self.assertTrue(response.context['preview_can_approve'])
        decision_url = response.context['preview_approve_url']
        self.assertContains(self.client.get(decision_url), 'Одобрить и опубликовать')
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)
        self.assertEqual(self.client.post(decision_url).status_code, 302)
        self.place.refresh_from_db(); self.item.refresh_from_db(); revision.refresh_from_db()
        self.assertTrue(self.place.is_public)
        self.assertEqual(self.place.description_ru, proposed)
        self.assertEqual(self.item.status, 'APPROVED')
        self.assertEqual(revision.status, 'approved')
        self.assertFalse(self.client.get(self.url).context['preview_can_moderate'])
