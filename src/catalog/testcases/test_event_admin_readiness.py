from datetime import timedelta
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils import timezone, translation
from catalog.models import Event, Organization
from catalog.domain_admin.place import EventAdmin
from catalog.testcases import admin as legacy_admin

class EventAdminReadinessTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser('event-readiness', 'event@example.invalid', 'synthetic')
        self.admin = EventAdmin(Event, AdminSite())
        self.request = RequestFactory().get('/admin/catalog/event/add/')
        self.request.user = self.actor
        self.org = Organization.objects.create(owner=self.actor, name_az='Synthetic organizer')

    def form(self, event=None, data=None):
        return self.admin.get_form(self.request, event)(instance=event, data=data)

    def event(self, **changes):
        start = timezone.now() + timedelta(days=20)
        values = dict(name='Synthetic event', name_az='Synthetic event', category_id='EDU',
                      description_az='Synthetic description', organizer_organization=self.org,
                      event_format='online', status='draft', start_datetime=start,
                      end_datetime=start+timedelta(hours=1), phone='+994501234567', photo='events/synthetic.jpg')
        values.update(changes)
        return Event.objects.create(**values)

    def summary(self, event=None, form=None):
        return self.admin._build_event_form_summary(form=form or self.form(event), obj=event, add=event is None)

    def test_global_russian_labels(self):
        with translation.override('ru'):
            for value in ['Владелец мероприятия','Связанное место','Нужна доработка','Готово к публикации','Дата окончания','Завершено']:
                self.assertEqual(translation.gettext(value), value)

    def test_new_card_has_requirements_and_new_lifecycle(self):
        with translation.override('ru'):
            summary = self.summary()
            self.assertGreater(summary['total'], 0)
            self.assertEqual(summary['visibility']['label'], 'Новая карточка')
            self.assertFalse(summary['server_ready'])

    def test_online_readiness_matches_publication_and_has_no_address(self):
        event = self.event()
        summary = self.summary(event)
        self.assertTrue(summary['server_ready'])
        self.assertNotIn('address', [i['field_name'] for i in summary['checklist_items']])
        self.assertEqual(summary['completion_pct'], 100)

    def test_ru_name_cannot_replace_required_az_name(self):
        event = self.event(name_az='', name_ru='Russian title')
        summary = self.summary(event)
        self.assertFalse(summary['server_ready'])
        self.assertLess(summary['completion_pct'], 100)

    def test_invalid_interval_cannot_show_ready(self):
        event = self.event()
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data['end_datetime'] = data['start_datetime']
        form = self.form(event, data)
        self.assertFalse(form.is_valid())
        self.assertFalse(self.summary(event, form)['server_ready'])

    def test_lifecycle_draft_pending_published_rejected(self):
        with translation.override('ru'):
            for status, label in [('draft','Черновик'),('pending','На модерации'),('published','Опубликовано'),('rejected','Отклонено')]:
                event = self.event(status=status)
                self.assertEqual(self.summary(event)['visibility']['label'], label)

    def test_draft_post_and_publication_error_keep_data(self):
        self.client.force_login(self.actor)
        event = self.event(phone='', photo='')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data['_save_draft'] = '1'
        response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
        self.assertEqual(response.status_code, 302)
        data.pop('_save_draft'); data['_publish_event']='1'
        response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.errors)
        event.refresh_from_db(); self.assertEqual(event.status, 'draft')

    def test_contact_fields_are_rendered_for_add_and_edit(self):
        self.client.force_login(self.actor)
        event = self.event()
        for url in ['/admin/catalog/event/add/', f'/admin/catalog/event/{event.pk}/change/']:
            response = self.client.get(url)
            for name in ['phone', 'instagram', 'website', 'moderation_note']:
                self.assertContains(response, f'name="{name}"')

    def test_failed_upload_does_not_preview_unsaved_file_as_stored(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.actor)
        event = self.event()
        image = io.BytesIO(); Image.new('RGB', (20, 20)).save(image, format='PNG')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(website='invalid-url', _continue='1', photo=SimpleUploadedFile('fresh-local.png', image.getvalue(), content_type='image/png'))
        response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.errors)
        self.assertNotContains(response, 'src="/media/fresh-local.png"')
        self.assertContains(response, 'data-main-photo-initial-url="/media/events/synthetic.jpg"')

    def test_shared_translation_consumers(self):
        from catalog.models import Place
        from catalog.forms import OwnerEventForm
        from catalog.services.volunteer_dashboard import STATES
        with translation.override('ru'):
            self.assertEqual(str(Event._meta.get_field('owner').verbose_name), 'Владелец мероприятия')
            self.assertEqual(str(Event._meta.get_field('related_place').verbose_name), 'Связанное место')
            self.assertEqual(str(OwnerEventForm.base_fields['related_place'].label), 'Связанное место')
            self.assertEqual(str(OwnerEventForm.base_fields['end_date'].label), 'Дата окончания')
            self.assertEqual(Place(status='needs_changes').get_status_display(), 'Нужна доработка')
            self.assertEqual(str(STATES['rejected'][0]), 'Нужна доработка')

    def test_failed_publication_keeps_saved_lifecycle_in_summary(self):
        self.client.force_login(self.actor)
        event = self.event(phone='', photo='')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(status='published', _continue='1')
        with translation.override('ru'):
            response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
            self.assertEqual(response.status_code, 200)
            summary = response.context['km_event_form_summary']
            self.assertFalse(summary['visibility']['is_public'])
            self.assertEqual(summary['visibility']['label'], 'Черновик')
        event.refresh_from_db(); self.assertEqual(event.status, 'draft')
