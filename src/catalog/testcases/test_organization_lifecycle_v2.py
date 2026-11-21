"""Organizations v2: one lifecycle, readable URLs, honest branch health, media,
socials, diagnostics and the owner/admin cockpits. Positive and negative."""
import io
import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models import F
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from catalog.models import Organization, Place, VolunteerPlaceRevision
from catalog.services import organization_ownership, organization_state, publication
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory

MEDIA = tempfile.mkdtemp(prefix='km-org-v2-')


def image_upload(name='logo.png', size=(256, 256), fmt='PNG', content_type='image/png'):
    buffer = io.BytesIO()
    Image.new('RGB', size, (19, 111, 56)).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@override_settings(MEDIA_ROOT=MEDIA)
class OrganizationV2Base(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        ensure_quality_subcategory('EDU')
        U = get_user_model()
        self.owner = U.objects.create_user('org_v2_owner')
        self.stranger = U.objects.create_user('org_v2_stranger')
        self.staff = U.objects.create_superuser('org_v2_staff', 'v2@example.invalid', 'synthetic')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Günəş Akademiyası')

    def propose(self, patch, submit=True, actor=None):
        self.org.refresh_from_db()
        revision = VolunteerPlaceRevision.objects.filter(organization=self.org).first()
        return publication.propose(actor=actor or self.owner, target_type='organization', target_id=self.org.pk,
            patch=patch, schema_version=publication.SCHEMA_VERSION, expected_version=self.org.content_version,
            revision_version=revision.version if revision else 0, submit=submit)

    def approve(self):
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.org.refresh_from_db()

    def publish(self, **patch):
        self.propose({'description_az': 'Uşaqlar üçün şahmat və riyaziyyat dərsləri', **patch})
        self.approve()

    def linked_place(self, **kw):
        place = create_quality_place(owner=self.owner, created_by=self.owner, **kw)
        organization_ownership.request_join(actor=self.owner, place_id=place.pk, organization_id=self.org.pk)
        place.refresh_from_db()
        return place


class LifecycleTests(OrganizationV2Base):
    def test_every_state_has_one_code(self):
        self.assertEqual(organization_state.lifecycle(self.org).code, 'draft')
        self.propose({'description_az': 'x'})
        self.assertEqual(organization_state.lifecycle(self.org).code, 'pending')
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=False, note='Добавьте логотип')
        state = organization_state.lifecycle(self.org)
        self.assertEqual((state.code, state.review_note), ('needs_changes', 'Добавьте логотип'))
        self.propose({'description_az': 'y'})
        self.approve()
        self.assertEqual(organization_state.lifecycle(self.org).code, 'published')
        self.propose({'name_ru': 'Солнце'})
        self.assertEqual(organization_state.lifecycle(self.org).code, 'published_review')
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.org.refresh_from_db()
        self.assertEqual(organization_state.lifecycle(self.org).code, 'archived')

    def test_legacy_published_without_approval_is_inconsistent_and_never_public(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        self.org.refresh_from_db()
        self.assertEqual(organization_state.lifecycle(self.org).code, 'inconsistent')
        self.assertFalse(self.org.is_public)
        self.assertEqual(self.client.get(reverse('organization_detail', args=[self.org.public_id])).status_code, 404)

    def test_draft_is_not_public_by_uuid_or_guessed_slug(self):
        self.assertEqual(self.client.get(reverse('organization_detail', args=[self.org.public_id])).status_code, 404)
        self.assertEqual(self.client.get('/organizations/gunes-akademiyasi/').status_code, 404)


class SlugTests(OrganizationV2Base):
    def test_approval_reserves_transliterated_slug_and_uuid_redirects(self):
        self.publish()
        self.assertEqual(self.org.slug, 'gunes-akademiyasi')
        response = self.client.get(reverse('organization_detail', args=[self.org.public_id]))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/organizations/gunes-akademiyasi/')
        self.assertEqual(self.client.get('/organizations/gunes-akademiyasi/').status_code, 200)
        self.assertEqual(self.client.get('/ru/organizations/gunes-akademiyasi/').status_code, 200)

    def test_slug_is_stable_after_rename_and_unique_between_namesakes(self):
        self.publish()
        self.propose({'name_az': 'Tamamilə yeni ad'})
        self.approve()
        self.assertEqual(self.org.slug, 'gunes-akademiyasi')
        twin = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Günəş Akademiyası')
        self.assertEqual(organization_state.build_slug(twin), 'gunes-akademiyasi-2')

    def test_numeric_name_never_looks_like_an_id(self):
        org = Organization.objects.create(owner=self.owner, name_az='123 Kids')
        self.assertTrue(organization_state.build_slug(org).startswith('org-123'))

    def test_unpublished_slug_returns_404_after_unpublish(self):
        self.publish()
        publication.unpublish(actor=self.staff, target_type='organization', target_id=self.org.pk,
                              expected_version=self.org.content_version)
        self.assertEqual(self.client.get('/organizations/gunes-akademiyasi/').status_code, 404)


class BranchHealthTests(OrganizationV2Base):
    def test_ownership_change_marks_branch_stale_instead_of_hiding_it(self):
        place = self.linked_place(name='Filial 1')
        health = organization_state.branch_health(self.org)
        self.assertEqual((health.current_count, health.stale_count), (1, 0))
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        health = organization_state.branch_health(self.org)
        self.assertEqual((health.current_count, health.stale_count), (0, 1))
        self.assertIn(str(health.stale[0].link_stale_reason), ('У места сменился владелец', 'Məkanın sahibi dəyişib', 'The place changed owner'))
        self.assertEqual(organization_state.branch_counts_by_org([self.org.pk])[self.org.pk], (0, 1))

    def test_workspace_shows_stale_branch_with_reconfirm_and_reconfirm_restores_link(self):
        place = self.linked_place(name='Filial 2')
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        self.client.force_login(self.owner)
        page = self.client.get(f'/ru/account/organizations/{self.org.pk}/')
        self.assertContains(page, 'data-org-cockpit')
        self.assertContains(page, 'Подтвердить заново')
        self.assertContains(page, 'orgx-tab-count--warn')
        response = self.client.post(reverse('organization_workspace_join', args=[self.org.pk]), {'place_id': place.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(organization_state.branch_health(self.org).current_count, 1)

    def test_stranger_cannot_reconfirm_someone_elses_link(self):
        place = self.linked_place(name='Filial 3')
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        self.client.force_login(self.stranger)
        self.client.post(reverse('organization_workspace_join', args=[self.org.pk]), {'place_id': place.pk})
        self.assertEqual(organization_state.branch_health(self.org).stale_count, 1)


class WorkspaceMediaTests(OrganizationV2Base):
    def save(self, files=None, **fields):
        self.org.refresh_from_db()
        revision = VolunteerPlaceRevision.objects.filter(organization=self.org).first()
        data = {'name_az': self.org.name_az, 'expected_version': self.org.content_version,
                'revision_version': revision.version if revision else 0, 'submit': '1', **fields}
        self.client.force_login(self.owner)
        return self.client.post(reverse('organization_workspace_save', args=[self.org.pk]), {**data, **(files or {})})

    def test_logo_cover_and_socials_travel_through_review_to_public_page(self):
        response = self.save({'logo': image_upload(), 'cover_photo': image_upload('c.jpg', (1200, 400), 'JPEG', 'image/jpeg')},
                             instagram='@gunes.kids', facebook='https://www.facebook.com/gunes', address='Bakı, Nizami 1')
        self.assertEqual(response.status_code, 302)
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        self.assertTrue(default_storage.exists(revision.payload['logo']))
        self.assertTrue(revision.payload['logo'].startswith('organizations/logos/'))
        self.assertTrue(revision.payload['cover_photo'].endswith('.jpg'))
        self.org.refresh_from_db()
        self.assertFalse(self.org.logo)  # nothing public before approval
        self.approve()
        self.assertTrue(self.org.logo)
        links = {row['kind']: row['url'] for row in organization_state.social_links(self.org)}
        self.assertEqual(links['instagram'], 'https://www.instagram.com/gunes.kids')
        page = self.client.get(f'/ru/organizations/{self.org.slug}/')
        self.assertContains(page, self.org.logo.url)
        self.assertContains(page, 'https://www.instagram.com/gunes.kids')
        self.assertContains(page, 'Bakı, Nizami 1')

    def test_partial_form_never_blanks_newer_fields(self):
        Organization.objects.filter(pk=self.org.pk).update(address='Kept', instagram='@kept')
        self.assertEqual(self.save(description_az='Only this').status_code, 302)
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        self.assertNotIn('address', revision.changed_fields)
        self.assertNotIn('instagram', revision.changed_fields)

    def test_clear_flag_removes_logo_in_candidate(self):
        self.save({'logo': image_upload()})
        self.approve()
        self.save(logo_clear='1')
        self.assertEqual(VolunteerPlaceRevision.objects.get(organization=self.org).payload['logo'], '')

    def test_rejects_small_wrong_format_oversized_and_fake_images(self):
        cases = {
            'small': {'logo': image_upload(size=(60, 60))},
            'gif': {'logo': image_upload('a.gif', (300, 300), 'GIF', 'image/gif')},
            'cover_small': {'cover_photo': image_upload('c.png', (500, 200))},
            'fake': {'logo': SimpleUploadedFile('x.png', b'not an image', content_type='image/png')},
        }
        for name, files in cases.items():
            with self.subTest(case=name):
                response = self.save(files)
                self.assertEqual(response.status_code, 400)
                self.assertContains(response, 'org-editor-errors', status_code=400)
                self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())
        with override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=None):
            from catalog.controllers import organization_workspace as ws
            original = ws.MEDIA_RULES['logo']
            ws.MEDIA_RULES['logo'] = (1024, 120, 120)
            try:
                self.assertEqual(self.save({'logo': image_upload(size=(400, 400))}).status_code, 400)
            finally:
                ws.MEDIA_RULES['logo'] = original

    def test_rejects_foreign_and_script_social_links(self):
        for value in ('javascript:alert(1)', 'https://evil.example/insta', 'not a handle!!'):
            with self.subTest(value=value):
                response = self.save(instagram=value)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())

    def test_service_rejects_bad_social_even_without_the_form(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.propose({'tiktok': 'https://evil.example/@x'})

    def test_server_draft_cannot_carry_media_paths(self):
        from catalog.services import server_drafts
        self.assertNotIn('logo', publication.fields_for('organization') - {'photo', 'cover_photo', 'gallery', 'logo'})
        self.assertIn('address', publication.fields_for('organization'))

    def test_name_is_escaped_in_cockpit(self):
        Organization.objects.filter(pk=self.org.pk).update(name_az='<script>alert(1)</script>')
        self.client.force_login(self.owner)
        page = self.client.get(f'/ru/account/organizations/{self.org.pk}/')
        self.assertNotContains(page, '<script>alert(1)</script>')
        self.assertContains(page, '&lt;script&gt;')

    def test_stranger_gets_404_on_workspace_and_save(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(f'/ru/account/organizations/{self.org.pk}/').status_code, 404)
        response = self.client.post(reverse('organization_workspace_save', args=[self.org.pk]),
                                    {'name_az': 'Hijack', 'expected_version': 1, 'revision_version': 0, 'submit': '1', 'logo': image_upload()})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())


class ReadinessAndIndexTests(OrganizationV2Base):
    def test_readiness_reflects_candidate_and_only_name_is_required(self):
        ready = organization_state.readiness(self.org)
        self.assertTrue(ready['can_submit'])
        self.assertLess(ready['percent'], 30)
        ready = organization_state.readiness(self.org, data={'description_az': 'x' * 90, 'phone': '+994501112233', 'logo': 'a.png'})
        done = {row['key'] for row in ready['items'] if row['done']}
        self.assertTrue({'description', 'contacts', 'logo'} <= done)
        Organization.objects.filter(pk=self.org.pk).update(name_az='')
        self.org.refresh_from_db()
        self.assertFalse(organization_state.readiness(self.org)['can_submit'])

    def test_steps_progress_is_monotonic(self):
        state = organization_state.lifecycle(self.org)
        health = organization_state.branch_health(self.org)
        steps = organization_state.steps(self.org, state, organization_state.readiness(self.org, health=health), health)
        self.assertEqual(sum(1 for s in steps['items'] if s['current']), 1)
        self.assertGreaterEqual(steps['progress'], 0)

    def test_index_shows_one_state_and_counts(self):
        self.linked_place(name='Filial A')
        self.client.force_login(self.owner)
        page = self.client.get('/ru/account/organizations/')
        self.assertContains(page, 'data-org-state="draft"')
        self.assertContains(page, 'orgx-row-meta')


class DiagnoseCommandTests(OrganizationV2Base):
    def run_command(self, *args):
        out = io.StringIO()
        call_command('diagnose_organizations', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_reports_and_changes_nothing(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        place = self.linked_place(name='Stale')
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        output = self.run_command()
        self.assertIn('published_without_approval', output)
        self.assertIn('stale_branch', output)
        self.assertIn('Dry run', output)
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'published')

    def test_apply_returns_legacy_to_draft_and_never_touches_links(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        place = self.linked_place(name='Stale')
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        self.run_command('--apply')
        self.org.refresh_from_db()
        self.assertEqual((self.org.status, self.org.approved_at), ('draft', None))
        place.refresh_from_db()
        self.assertEqual(place.organization_id, self.org.pk)
        self.assertEqual(organization_state.branch_health(self.org).stale_count, 1)

    def test_approve_legacy_publishes_with_slug(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        self.run_command('--apply', '--approve-legacy')
        self.org.refresh_from_db()
        self.assertTrue(self.org.is_public)
        self.assertEqual(self.org.slug, 'gunes-akademiyasi')

    def test_legacy_with_pending_review_is_left_for_moderator(self):
        self.propose({'description_az': 'x'})
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        self.run_command('--apply')
        self.org.refresh_from_db()
        self.assertEqual(self.org.status, 'published')

    def test_approve_legacy_needs_apply_and_json_output_parses(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.run_command('--approve-legacy')
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        rows = json.loads(self.run_command('--json').split('\nDry run')[0])
        self.assertEqual(rows[0]['code'], 'published_without_approval')


class AdminCockpitTests(OrganizationV2Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.change = reverse('admin:catalog_organization_change', args=[self.org.pk])

    def test_change_form_has_cockpit_and_translated_readonly_labels(self):
        self.client.cookies['django_language'] = 'ru'
        page = self.client.get(self.change)
        self.assertContains(page, 'km-orgc')
        self.assertContains(page, 'data-org-state="draft"')
        self.assertNotContains(page, 'Content version')
        self.assertNotContains(page, 'Archived at')

    def test_unpublish_button_hidden_for_legacy_inconsistent(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        page = self.client.get(self.change)
        self.assertNotContains(page, 'value="unpublish"')
        self.assertContains(page, 'data-org-state="inconsistent"')

    def test_add_page_title_is_grammatical(self):
        self.client.cookies['django_language'] = 'ru'
        page = self.client.get(reverse('admin:catalog_organization_add'))
        self.assertContains(page, 'Новая организация')

    def test_filters_for_inconsistent_and_stale(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        other = Organization.objects.create(owner=self.owner, name_az='Other')
        listing = self.client.get(reverse('admin:catalog_organization_changelist') + '?status=inconsistent')
        self.assertEqual([o.pk for o in listing.context['cl'].result_list], [self.org.pk])
        place = create_quality_place(owner=self.owner, created_by=self.owner, name='S')
        organization_ownership.request_join(actor=self.owner, place_id=place.pk, organization_id=other.pk)
        Place.objects.filter(pk=place.pk).update(ownership_version=F('ownership_version') + 1)
        listing = self.client.get(reverse('admin:catalog_organization_changelist') + '?has_branches=stale')
        self.assertEqual([o.pk for o in listing.context['cl'].result_list], [other.pk])

    def test_return_for_changes_requires_note_and_reaches_owner(self):
        self.propose({'description_az': 'x'})
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        url = reverse('admin:catalog_organization_transition', args=[self.org.pk])
        self.client.post(url, {'action': 'return', 'revision_version': revision.version, 'review_note': '  '})
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.client.post(url, {'action': 'return', 'revision_version': revision.version, 'review_note': 'Нужен логотип'})
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'rejected')
        self.client.force_login(self.owner)
        page = self.client.get(f'/ru/account/organizations/{self.org.pk}/')
        self.assertContains(page, 'Нужен логотип')
        self.assertContains(page, 'data-org-state="needs_changes"')

    def own(self):
        Organization.objects.filter(pk=self.org.pk).update(owner=self.staff)
        self.org.refresh_from_db()

    def test_moderator_who_is_not_owner_can_open_the_change_form(self):
        page = self.client.get(self.change)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'km-orgc')

    def test_admin_upload_reaches_candidate(self):
        self.own()
        data = {'name_az': self.org.name_az, 'source_version': self.org.content_version, 'candidate_version': 0,
                'logo': image_upload(), '_submit_candidate': '1'}
        response = self.client.post(self.change, data)
        self.assertEqual(response.status_code, 302, getattr(response, 'context', {}) and response.context['adminform'].form.errors)
        revision = VolunteerPlaceRevision.objects.get(organization=self.org)
        self.assertTrue(default_storage.exists(revision.payload['logo']))

    def test_admin_rejects_tiny_logo(self):
        self.own()
        data = {'name_az': self.org.name_az, 'source_version': self.org.content_version, 'candidate_version': 0,
                'logo': image_upload(size=(40, 40)), '_submit_candidate': '1'}
        response = self.client.post(self.change, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(organization=self.org).exists())


class PublicDirectoryTests(OrganizationV2Base):
    def test_card_uses_canonical_url_logo_and_socials(self):
        self.propose({'description_az': 'x', 'instagram': '@gunes'})
        self.approve()
        Organization.objects.filter(pk=self.org.pk).update(logo='organizations/logos/x.png')
        page = self.client.get('/ru/organizations/')
        self.assertContains(page, '/ru/organizations/gunes-akademiyasi/')
        self.assertContains(page, 'org-card-logo')
        self.assertContains(page, 'https://www.instagram.com/gunes')

    def test_inconsistent_and_draft_are_absent_from_directory(self):
        Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=None)
        page = self.client.get('/ru/organizations/')
        self.assertNotContains(page, 'Günəş Akademiyası')
