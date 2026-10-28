"""Entry speed must not weaken Event publication, organizer ACL or history."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.forms import OwnerEventForm
from catalog.models import Category, Event, Organization, Place, SiteSettings
from catalog.services import event_domain
from catalog.services.event_queries import query_public_events


class EventPresentationTests(SimpleTestCase):
    def test_upper_age_bound_is_not_presented_as_one_exact_age(self):
        event = Event(age_to=12)
        for language, expected in [('ru','до 12'),('az','12-dək'),('en','up to 12')]:
            with self.subTest(language=language), translation.override(language):
                self.assertEqual(event.age_display, expected)


class EventEfficiencyBackendTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('efficient-event-owner')
        self.other = get_user_model().objects.create_user('efficient-event-other')
        self.org = Organization.objects.create(name_az='Synthetic organizer', owner=self.owner)
        self.category = Category.objects.create(code='efficient-event', name_az='Synthetic category')
        site = SiteSettings.get_solo()
        site.events_section_enabled = True
        site.save()

    def event(self, **extra):
        values = dict(name_az='Synthetic workshop', category_id=self.category.code,
            organizer_organization_id=self.org.pk, event_format='online',
            start_datetime=timezone.now()+timedelta(days=3),
            end_datetime=timezone.now()+timedelta(days=3, hours=1),
            description_az='Synthetic description', phone='+994501234567',
            price_text='Ödənişsiz / Бесплатно', photo='events/synthetic-shared.jpg')
        values.update(extra)
        return event_domain.create_event(actor=self.owner, values=values)

    def test_mixed_free_label_is_found_without_matching_paid_prose(self):
        free = self.event()
        paid = self.event(price_text='Free entry, workshop 15 AZN')
        Event.objects.filter(pk__in=[free.pk, paid.pk]).update(status='published')
        self.assertEqual(list(query_public_events({'free':'1'}).values_list('pk', flat=True)), [free.pk])
        self.assertTrue(getattr(free, 'is_free', False))
        self.assertFalse(getattr(paid, 'is_free', False))

    def test_typed_price_overrides_legacy_text_and_validates_ranges(self):
        event = self.event()
        event.price_mode = 'range'
        event.price_amount = Decimal('15')
        event.price_amount_max = Decimal('25')
        event.price_currency = 'AZN'
        with translation.override('ru'):
            self.assertEqual(event.price_display, '15–25 AZN')
        for mode, amount, maximum in [('fixed', -1, None), ('range', 25, 15), ('from', None, None)]:
            with self.subTest(mode=mode), self.assertRaises(ValidationError):
                event_domain.save_event(actor=self.owner, event_id=event.pk,
                    expected_updated_at=event.updated_at.isoformat(),
                    values={'price_mode':mode, 'price_amount':amount, 'price_amount_max':maximum})

    def test_registration_uses_selected_channel_and_never_infers_whatsapp(self):
        event = self.event()
        self.assertEqual(getattr(event, 'registration', {}).get('url'), 'tel:+994501234567')
        event.registration_method = 'whatsapp'
        event.whatsapp = '+13104564918'
        self.assertEqual(event.registration['url'], 'https://wa.me/13104564918')
        event.whatsapp = ''
        self.assertEqual(event.registration['url'], '')
        event.registration_method = 'link'
        event.registration_url = 'javascript:alert(1)'
        self.assertEqual(event.registration['url'], '')

    def test_submission_requires_photo_and_selected_contact_but_not_age_or_phone(self):
        event = self.event(photo='')
        with self.assertRaises(ValidationError):
            event_domain.submit_event(actor=self.owner, event_id=event.pk, expected_updated_at=event.updated_at.isoformat())
        event = self.event(phone='', registration_method='link', registration_url='https://example.test/register', price_mode='unknown')
        event = event_domain.submit_event(actor=self.owner, event_id=event.pk, expected_updated_at=event.updated_at.isoformat())
        self.assertEqual(event.status, 'pending')
        self.assertIsNone(event.age_from)

    def test_ended_event_cannot_be_newly_submitted(self):
        event = self.event(start_datetime=timezone.now()-timedelta(days=2), end_datetime=timezone.now()-timedelta(days=1))
        with self.assertRaises(ValidationError):
            event_domain.submit_event(actor=self.owner, event_id=event.pk, expected_updated_at=event.updated_at.isoformat())

    def test_single_eligible_organizer_defaults_without_accepting_foreign_organizer(self):
        form = OwnerEventForm(user=self.owner, draft_save_only=True,
            data={'category':self.category.code, 'event_format':'online'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['organizer_organization'], self.org)
        foreign = Organization.objects.create(name_az='Foreign', owner=self.other)
        form = OwnerEventForm(user=self.owner, draft_save_only=True,
            data={'category':self.category.code, 'event_format':'online', 'organizer_organization':foreign.pk})
        self.assertFalse(form.is_valid())

    def test_repeat_clears_occurrence_and_moderation_with_new_identity(self):
        source = self.event()
        source.status = 'published'
        source.save()
        source = event_domain.cancel_event(actor=self.owner,event_id=source.pk,
            expected_updated_at=source.updated_at.isoformat(), reason='Synthetic cancellation')
        token = source.updated_at
        repeated = event_domain.repeat_event(actor=self.owner,event_id=source.pk, expected_updated_at=token.isoformat())
        self.assertNotEqual(repeated.pk, source.pk)
        self.assertNotEqual(repeated.slug, source.slug)
        self.assertEqual(repeated.status, 'draft')
        self.assertEqual(repeated.occurrence_state, 'scheduled')
        self.assertEqual(repeated.occurrence_version, 0)
        self.assertEqual(repeated.occurrence_changes.count(), 0)
        self.assertIsNone(repeated.start_datetime)
        self.assertIsNone(repeated.end_datetime)
        self.assertIsNone(repeated.published_at)
        self.assertEqual(repeated.venue_snapshot, {})
        self.assertEqual(repeated.photo.name, source.photo.name)
        source.refresh_from_db()
        self.assertEqual(source.updated_at, token)
        self.assertEqual(source.occurrence_state, 'cancelled')
        self.assertEqual(source.occurrence_changes.count(), 1)

    def test_repeat_rejects_foreign_stale_and_get_requests(self):
        source = self.event()
        with self.assertRaises(PermissionDenied):
            event_domain.repeat_event(actor=self.other,event_id=source.pk,expected_updated_at=source.updated_at.isoformat())
        with self.assertRaises(ValidationError):
            event_domain.repeat_event(actor=self.owner,event_id=source.pk,expected_updated_at=(source.updated_at-timedelta(seconds=1)).isoformat())
        self.client.force_login(self.owner)
        url = reverse('owner_event_repeat', kwargs={'pk':source.pk})
        self.assertEqual(self.client.get(url).status_code,405)
        response = self.client.post(url, {'expected_updated_at':source.updated_at.isoformat()})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Event.objects.count(),2)

    def test_cancelled_is_absent_from_default_feed_but_keeps_detail(self):
        source = self.event()
        source.status = 'published'
        source.save()
        source = event_domain.cancel_event(actor=self.owner,event_id=source.pk,expected_updated_at=source.updated_at.isoformat(),reason='Synthetic cancellation')
        self.assertFalse(query_public_events().filter(pk=source.pk).exists())
        self.assertEqual(self.client.get(source.get_absolute_url()).status_code,200)
        self.assertTrue(query_public_events({'date':source.start_datetime.date().isoformat()}).filter(pk=source.pk).exists())

    def test_exact_child_age_accepts_one_sided_bounds_and_excludes_unknown(self):
        suitable = self.event(age_from=6)
        unsuitable = self.event(age_to=4)
        unknown = self.event()
        Event.objects.filter(pk__in=[suitable.pk,unsuitable.pk,unknown.pk]).update(status='published')
        self.assertEqual(list(query_public_events({'age':'7'}).values_list('pk',flat=True)),[suitable.pk])

    def test_owner_draft_edit_retains_existing_photo_without_upload_or_file_read(self):
        source = self.event()
        form = OwnerEventForm(user=self.owner, instance=source, draft_save_only=True,
            data={'category':self.category.code, 'event_format':'online',
                'organizer_organization':self.org.pk, 'expected_updated_at':source.updated_at.isoformat()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['photo'].name, 'events/synthetic-shared.jpg')

    def test_published_legacy_edit_retains_unchanged_bad_phone_but_republish_requires_readiness(self):
        from catalog.domain_admin.place import EventAdminForm
        source = self.event()
        Event.objects.filter(pk=source.pk).update(status='published', phone='old contact text',
            description_az='', photo='', price_text='')
        source.refresh_from_db()
        data = {'category':self.category.code, 'event_format':'online', 'name':'Updated title', 'name_az':'Updated title',
            'organizer_organization':self.org.pk, 'status':'published', 'phone':'old contact text',
            'start_datetime':source.start_datetime.isoformat(), 'end_datetime':source.end_datetime.isoformat(),
            'expected_updated_at':source.updated_at.isoformat()}
        form = EventAdminForm(instance=source, data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        source.refresh_from_db()
        self.assertEqual(source.phone, 'old contact text')
        form = EventAdminForm(instance=source, data={**data,'expected_updated_at':source.updated_at.isoformat(),'_publish_event':'1'})
        self.assertFalse(form.is_valid())

    def test_multiple_eligible_organizers_require_choice(self):
        Organization.objects.create(name_az='Second organizer', owner=self.owner)
        form = OwnerEventForm(user=self.owner, draft_save_only=True,
            data={'category':self.category.code, 'event_format':'online'})
        self.assertFalse(form.is_valid())

    def test_owner_venue_defaults_convert_float_coordinates_to_six_decimal_places(self):
        venue = Place.objects.create(name='Synthetic venue', category=self.category,
            owner=self.owner, address='Synthetic address', status='published')
        Place.objects.filter(pk=venue.pk).update(lat=40.4093, lng=49.8671)
        form = OwnerEventForm(user=self.owner, draft_save_only=True,
            data={'category':self.category.code, 'event_format':'physical',
                'organizer_organization':self.org.pk, 'related_place':venue.pk})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['lat'],Decimal('40.409300'))
        self.assertEqual(form.cleaned_data['lng'],Decimal('49.867100'))

    def test_duplicate_warning_is_nonblocking_and_scoped_to_organizer(self):
        from catalog.services.event_readiness import has_possible_duplicate
        source = self.event()
        duplicate = self.event(start_datetime=source.start_datetime, end_datetime=source.end_datetime)
        self.assertTrue(has_possible_duplicate(duplicate))
        duplicate.name_az='Different workshop'
        self.assertFalse(has_possible_duplicate(duplicate))
        duplicate.name_az=source.name_az
        duplicate.organizer_organization=Organization.objects.create(name_az='Other organizer', owner=self.other)
        self.assertFalse(has_possible_duplicate(duplicate))

    def test_review_only_approves_pending_and_requires_reviewer_authority(self):
        reviewer = get_user_model().objects.create_superuser('efficient-reviewer','reviewer@example.test','synthetic')
        event = self.event()
        with self.assertRaises(ValidationError):
            event_domain.review_event(actor=reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),decision='approve')
        Event.objects.filter(pk=event.pk).update(status='pending')
        event.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            event_domain.review_event(actor=self.owner,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),decision='approve')
        event = event_domain.review_event(actor=reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),decision='approve')
        self.assertEqual(event.status,'published')
        self.assertIsNotNone(event.published_at)

    def test_review_can_return_unresolved_or_archived_organizer_but_not_approve(self):
        reviewer = get_user_model().objects.create_superuser('efficient-return-reviewer','returns@example.test','synthetic')
        unresolved = Event.objects.create(category=self.category,name='Unresolved event',status='pending')
        with self.assertRaises(ValidationError):
            event_domain.review_event(actor=reviewer,event_id=unresolved.pk,expected_updated_at=unresolved.updated_at.isoformat(),decision='approve')
        with self.assertRaises(ValidationError):
            event_domain.review_event(actor=reviewer,event_id=unresolved.pk,expected_updated_at=unresolved.updated_at.isoformat(),decision='return',reason=' ')
        rejected = event_domain.review_event(actor=reviewer,event_id=unresolved.pk,expected_updated_at=unresolved.updated_at.isoformat(),decision='return',reason='Choose a current organizer')
        self.assertEqual(rejected.status,'rejected')
        self.assertEqual(rejected.rejection_reason,'Choose a current organizer')
        archived = self.event()
        Event.objects.filter(pk=archived.pk).update(status='pending')
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        archived.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            event_domain.review_event(actor=reviewer,event_id=archived.pk,expected_updated_at=archived.updated_at.isoformat(),decision='approve')
        returned = event_domain.review_event(actor=reviewer,event_id=archived.pk,expected_updated_at=archived.updated_at.isoformat(),decision='return',reason='Organizer unavailable')
        self.assertEqual(returned.status,'rejected')
