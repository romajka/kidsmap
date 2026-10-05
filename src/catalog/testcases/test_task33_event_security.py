"""Independent stage26 negative boundaries, synthetic records only."""
import json
import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.utils import timezone

from catalog.models import Category, Event, EventReview, Organization, Place, SiteSettings, Specialist
from catalog.services import review_versions
from catalog.testcases.utils import create_quality_place


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=0)
class EventSecurityTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.organizer = users.objects.create_user('security26-organizer')
        self.venue_owner = users.objects.create_user('security26-venue')
        self.other = users.objects.create_user('security26-other')
        self.staff = users.objects.create_user('security26-staff', is_staff=True)
        self.reviewer = users.objects.create_superuser('security26-reviewer', 'synthetic@example.test', 'synthetic')
        self.category = Category.objects.first() or Category.objects.create(code='SEC26', name_az='Synthetic')
        self.org = Organization.objects.create(owner=self.organizer, name_az='Synthetic organizer')
        self.venue = create_quality_place(owner=self.venue_owner)
        self.person = Specialist.objects.create(name='Synthetic verified person',
            verified_person_user=self.organizer, person_verified_at=timezone.now(),
            consultation_format='online', status='published', is_active=True)
        site = SiteSettings.get_solo()
        site.events_section_enabled = True
        site.save()

    def event(self, **changes):
        values = dict(name='Synthetic event', name_az='Synthetic event', category=self.category,
            organizer_organization=self.org, owner=self.venue_owner, event_format='online',
            start_datetime=timezone.now()+timedelta(days=2),
            end_datetime=timezone.now()+timedelta(days=2, hours=1))
        values.update(changes)
        return Event.objects.create(**values)

    def test_venue_legacy_owner_and_plain_staff_cannot_save_or_cancel_resolved_event(self):
        from catalog.services import event_domain
        event = self.event()
        for actor in (self.venue_owner, self.other, self.staff):
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionDenied):
                event_domain.save_event(actor=actor, event_id=event.pk,
                    values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionDenied):
                event_domain.cancel_event(actor=actor, event_id=event.pk,
                    expected_updated_at=event.updated_at.isoformat(), reason='FORGED')
        event.refresh_from_db()
        self.assertEqual(event.name_az, 'Synthetic event')
        self.assertEqual(event.occurrence_state, 'scheduled')

    def test_organization_transfer_revokes_stale_actor_and_old_event_owner(self):
        from catalog.services import event_domain
        event = self.event(owner=self.organizer)
        Organization.objects.filter(pk=self.org.pk).update(owner=self.other, ownership_version=2)
        with self.assertRaises(PermissionDenied):
            event_domain.save_event(actor=self.organizer, event_id=event.pk,
                values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())
        event_domain.save_event(actor=self.other, event_id=event.pk,
            values={'name_az': 'New owner edit'}, expected_updated_at=event.updated_at.isoformat())
        event.refresh_from_db()
        self.assertEqual(event.name_az, 'New owner edit')

    def test_deactivated_actor_is_reloaded_before_service_mutation(self):
        from catalog.services import event_domain
        event = self.event()
        get_user_model().objects.filter(pk=self.organizer.pk).update(is_active=False)
        self.assertTrue(self.organizer.is_active)
        with self.assertRaises(PermissionDenied):
            event_domain.save_event(actor=self.organizer, event_id=event.pk,
                values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())

    def test_stale_revision_cannot_overwrite_saved_edit_or_cancel(self):
        from catalog.services import event_domain
        event = self.event()
        old = event.updated_at.isoformat()
        event_domain.save_event(actor=self.organizer, event_id=event.pk,
            values={'name_az': 'Fresh edit'}, expected_updated_at=old)
        for action in ('save', 'cancel'):
            with self.subTest(action=action), self.assertRaises(ValidationError) as raised:
                if action == 'save':
                    event_domain.save_event(actor=self.organizer, event_id=event.pk,
                        values={'name_az': 'FORGED'}, expected_updated_at=old)
                else:
                    event_domain.cancel_event(actor=self.organizer, event_id=event.pk,
                        expected_updated_at=old, reason='FORGED')
            self.assertEqual(raised.exception.code, 'stale_version')
        event.refresh_from_db()
        self.assertEqual(event.name_az, 'Fresh edit')
        self.assertEqual(event.occurrence_state, 'scheduled')

    def test_verified_person_inactive_profile_cannot_create_or_edit(self):
        from catalog.services import event_domain
        event = self.event(organizer_organization=None, organizer_specialist=self.person)
        Specialist.objects.filter(pk=self.person.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            event_domain.save_event(actor=self.organizer, event_id=event.pk,
                values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())

    def test_organizer_ids_cannot_be_forged_for_foreign_organization_or_person(self):
        from catalog.services import event_domain
        foreign_org = Organization.objects.create(owner=self.other, name_az='Foreign organizer')
        foreign_person = Specialist.objects.create(name='Foreign person', verified_person_user=self.other,
            person_verified_at=timezone.now(), status='published', is_active=True)
        for patch in ({'organizer_organization_id': foreign_org.pk}, {'organizer_specialist_id': foreign_person.pk}):
            with self.subTest(patch=patch), self.assertRaises(PermissionDenied):
                event_domain.create_event(actor=self.organizer, values={
                    'name_az': 'FORGED', 'category_id': self.category.code, 'event_format': 'online',
                    'start_datetime': timezone.now()+timedelta(days=2),
                    'end_datetime': timezone.now()+timedelta(days=2, hours=1), **patch})

    def test_platform_publication_permission_never_grants_organizer_edit(self):
        from catalog.services import event_domain
        self.staff.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_event'))
        event = self.event()
        self.assertFalse(event_domain.can_manage_event(self.staff, event))
        with self.assertRaises(PermissionDenied):
            event_domain.save_event(actor=self.staff, event_id=event.pk,
                values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())
        with self.assertRaises(PermissionDenied):
            event_domain.publish_event(actor=self.organizer, event_id=event.pk,
                expected_updated_at=event.updated_at.isoformat())

    def test_organizer_cannot_reassign_event_to_foreign_target_through_save(self):
        from catalog.services import event_domain
        event = self.event()
        foreign = Organization.objects.create(owner=self.other, name_az='Foreign organizer')
        with self.assertRaises(ValidationError):
            event_domain.save_event(actor=self.organizer, event_id=event.pk,
                values={'organizer_organization_id': foreign.pk}, expected_updated_at=event.updated_at.isoformat())
        event.refresh_from_db()
        self.assertEqual(event.organizer_organization_id, self.org.pk)

    def test_foreign_private_venue_id_cannot_capture_or_publish_secret_address(self):
        from catalog.services import event_domain
        Place.objects.filter(pk=self.venue.pk).update(status='draft', address='SECRET FOREIGN PRIVATE ADDRESS')
        values = {'name_az': 'Synthetic event', 'description_az': 'Synthetic event description',
            'category_id': self.category.code, 'organizer_organization_id': self.org.pk,
            'event_format': 'physical', 'related_place_id': self.venue.pk,
            'start_datetime': timezone.now()+timedelta(days=2),
            'end_datetime': timezone.now()+timedelta(days=2, hours=1)}
        with self.assertRaises(PermissionDenied):
            event_domain.create_event(actor=self.organizer, values=values)
        event = self.event(event_format='physical', related_place=self.venue,
            description_az='Synthetic event description', status='pending')
        with self.assertRaises(PermissionDenied):
            event_domain.publish_event(actor=self.reviewer, event_id=event.pk,
                expected_updated_at=event.updated_at.isoformat())
        event.refresh_from_db()
        self.assertNotEqual(event.status, 'published')
        self.assertNotIn('SECRET FOREIGN PRIVATE ADDRESS', json.dumps(event.venue_snapshot))

    def test_venue_privacy_is_rechecked_at_snapshot_after_initial_validation(self):
        """Deterministic stale-read injection; not a cross-connection race proof."""
        from catalog.services import event_domain
        Place.objects.filter(pk=self.venue.pk).update(status='published', address='Synthetic public address')
        event = self.event(event_format='physical', related_place=self.venue,
            description_az='Synthetic event description', status='pending')
        validate = event_domain._validate
        changed = False

        def validate_then_change(*args, **kwargs):
            nonlocal changed
            result = validate(*args, **kwargs)
            if not changed:
                changed = True
                Place.objects.filter(pk=self.venue.pk).update(status='draft',
                    address='SECRET NEW PRIVATE ADDRESS')
            return result

        with patch.object(event_domain, '_validate', side_effect=validate_then_change):
            with self.assertRaises(PermissionDenied):
                event_domain.publish_event(actor=self.reviewer, event_id=event.pk,
                    expected_updated_at=event.updated_at.isoformat())
        event.refresh_from_db()
        self.assertNotEqual(event.status, 'published')
        self.assertNotIn('SECRET NEW PRIVATE ADDRESS', json.dumps(event.venue_snapshot))

    def test_person_verification_revocation_and_legacy_owner_cannot_manage(self):
        from catalog.services import event_domain
        event = self.event(organizer_organization=None, organizer_specialist=self.person)
        Specialist.objects.filter(pk=self.person.pk).update(person_verified_at=None)
        for actor in (self.organizer, self.venue_owner):
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionDenied):
                event_domain.save_event(actor=actor, event_id=event.pk,
                    values={'name_az': 'FORGED'}, expected_updated_at=event.updated_at.isoformat())

    def test_event_review_reply_follows_fresh_organizer_not_venue_or_legacy_owner(self):
        event = self.event(status='published')
        head = EventReview.objects.create(event=event, rating=5, text='Approved synthetic text',
            status='approved', is_approved=True)
        self.assertTrue(review_versions.business_can_respond(user=self.organizer, head=head))
        for actor in (self.venue_owner, self.staff, self.other):
            self.assertFalse(review_versions.business_can_respond(user=actor, head=head))
        Organization.objects.filter(pk=self.org.pk).update(owner=self.other, ownership_version=2)
        self.assertFalse(review_versions.business_can_respond(user=self.organizer, head=head))
        self.assertTrue(review_versions.business_can_respond(user=self.other, head=head))
        for actor in (self.organizer, self.venue_owner, self.staff):
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionError):
                review_versions.respond_to_review(head=head, actor=actor,
                    revision_id=head.current_revision_id, kind='reply', text='FORGED')
        reply = review_versions.respond_to_review(head=head, actor=self.other,
            revision_id=head.current_revision_id, kind='reply', text='Fresh organizer response')
        self.assertEqual(reply.actor_id, self.other.pk)
        self.assertEqual(head.current_revision.responses.count(), 1)

    def test_foreign_event_delete_and_submit_http_boundaries_and_csrf(self):
        event = self.event()
        self.client.force_login(self.venue_owner)
        for action in ('delete', 'submit-review'):
            response = self.client.post('/ru/account/places/events/%s/%s/' % (event.pk, action))
            self.assertEqual(response.status_code, 403)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.organizer)
        self.assertEqual(csrf.post('/ru/account/places/events/%s/delete/' % event.pk).status_code, 403)
        event.refresh_from_db()
        self.assertIsNone(event.deleted_at)
        self.assertEqual(event.status, 'draft')

    def test_private_rejected_deleted_do_not_leak_public_detail_or_reviews(self):
        for changes in ({'status': 'draft'}, {'status': 'pending'}, {'status': 'rejected'},
                        {'status': 'published', 'deleted_at': timezone.now()}):
            event = self.event(**changes)
            with self.subTest(changes=changes):
                self.assertEqual(self.client.get('/ru'+event.get_absolute_url()).status_code, 404)
                self.assertEqual(self.client.get('/ru/reviews/event/target/%s/' % event.pk).status_code, 404)

    def test_review_pending_edit_and_foreign_target_never_change_page_schema_rating(self):
        event = self.event(status='published')
        foreign = self.event(status='published')
        head, revision = review_versions.submit_review(target=event, user=self.other,
            rating=5, text='APPROVED EVENT TEXT', author_name='Synthetic author')
        review_versions.moderate_candidate(head=head, revision_id=revision.pk, actor=self.reviewer, approve=True)
        review_versions.submit_review(target=event, user=self.other,
            rating=1, text='SECRET PENDING TEXT', author_name='Synthetic author')
        EventReview.objects.create(event=foreign, rating=1, text='FOREIGN TARGET TEXT',
            status='approved', is_approved=True)
        response = self.client.get('/ru'+event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        text = response.content.decode()
        self.assertNotIn('SECRET PENDING TEXT', text)
        self.assertNotIn('FOREIGN TARGET TEXT', text)
        scripts = re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', text, re.S)
        schemas = [json.loads(value) for value in scripts]
        schema = next(value for value in schemas if value.get('@type') == 'Event')
        self.assertEqual(schema['aggregateRating']['ratingValue'], 5)
        self.assertEqual(schema['aggregateRating']['reviewCount'], 1)
        page = self.client.get('/ru/reviews/event/target/%s/' % event.pk)
        self.assertContains(page, 'APPROVED EVENT TEXT')
        self.assertNotContains(page, 'SECRET PENDING TEXT')

    def test_public_jsonld_escapes_script_terminator_and_online_has_no_geo(self):
        payload = '</script><script id="security26-forged">FORGED</script>'
        event = self.event(status='published', name_az=payload, description_az=payload)
        response = self.client.get('/ru'+event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        text = response.content.decode()
        self.assertNotIn('<script id="security26-forged">', text)
        scripts = re.findall(r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', text, re.S)
        schema = next(json.loads(value) for value in scripts if json.loads(value).get('@type') == 'Event')
        self.assertEqual(schema['name'], payload)
        self.assertEqual(schema['location']['@type'], 'VirtualLocation')
        self.assertNotIn('geo', schema['location'])

    def test_admin_bulk_publication_checks_each_organizer_and_private_venue(self):
        from catalog.domain_admin.place import EventAdmin
        valid = self.event(description_az='Synthetic publishable online event')
        private = self.event(event_format='physical', related_place=self.venue,
            description_az='Synthetic private-venue event')
        Place.objects.filter(pk=self.venue.pk).update(status='draft', address='SECRET PRIVATE VENUE')
        person = self.event(organizer_organization=None, organizer_specialist=self.person,
            description_az='Synthetic unverified-person event')
        Specialist.objects.filter(pk=self.person.pk).update(person_verified_at=None)
        request = RequestFactory().post('/admin/catalog/event/', {'action': 'mark_published'})
        request.user = self.reviewer
        handler = EventAdmin(Event, AdminSite())
        with patch.object(handler, 'message_user'):
            handler.mark_published(request, Event.objects.filter(pk__in=[valid.pk, private.pk, person.pk]))
        valid.refresh_from_db(); private.refresh_from_db(); person.refresh_from_db()
        self.assertEqual(valid.status, 'published')
        self.assertEqual(valid.venue_snapshot, {})
        self.assertIsNone(valid.related_place_id)
        self.assertEqual(private.status, 'draft')
        self.assertEqual(person.status, 'draft')
        self.assertNotIn('SECRET PRIVATE VENUE', json.dumps(private.venue_snapshot))

    def test_admin_save_model_cannot_publish_without_platform_permission(self):
        from catalog.domain_admin.place import EventAdmin
        event = self.event(description_az='Synthetic event description')
        request = RequestFactory().post('/admin/catalog/event/', {'_publish_event': '1'})
        request.user = self.staff
        with self.assertRaises(PermissionDenied):
            EventAdmin(Event, AdminSite()).save_model(request, event, form=None, change=True)
        event.refresh_from_db()
        self.assertNotEqual(event.status, 'published')
        self.assertIsNone(event.published_at)

    def test_admin_draft_save_cannot_erase_approved_format_or_replace_past_dates(self):
        from catalog.domain_admin.place import EventAdmin
        event = self.event(status='published', start_datetime=timezone.now()-timedelta(days=2),
            end_datetime=timezone.now()-timedelta(days=1))
        request = RequestFactory().post('/admin/catalog/event/', {'_save_draft': '1'})
        request.user = self.reviewer
        handler = EventAdmin(Event, AdminSite())
        original_start = event.start_datetime
        event.start_datetime = timezone.now()+timedelta(days=2)
        event.end_datetime = timezone.now()+timedelta(days=3)
        with self.assertRaises(ValidationError):
            handler.save_model(request, event, form=None, change=True)
        event.refresh_from_db()
        self.assertEqual(event.start_datetime, original_start)
        event.event_format = 'physical'
        event.address = 'FORGED FORMAT HISTORY'
        with self.assertRaises(ValidationError):
            handler.save_model(request, event, form=None, change=True)
        event.refresh_from_db()
        self.assertEqual(event.event_format, 'online')
        self.assertEqual(event.venue_snapshot, {})

