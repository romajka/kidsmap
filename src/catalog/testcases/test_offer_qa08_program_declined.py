"""OFFER-QA-08: final decisions stay visible without reviving terminal proposals."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import override

from catalog.models import Activity, Organization, Program
from catalog.services import organization_ownership, publication
from catalog.testcases.utils import create_quality_place


class ProgramDeclinedTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('offer08_owner')
        self.outsider = users.objects.create_user('offer08_outsider')
        self.staff = users.objects.create_superuser('offer08_staff', 'offer08@example.invalid', 'fictional')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Fictional network')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.place.refresh_from_db()
        self.program = Program.objects.create(
            organization=self.org, created_by=self.owner, name_az='Fictional program',
            description_az='Approved', description_ru='Одобрено', status='published', approved_at=timezone.now(),
            category=self.place.category, subcategory=self.place.subcategory,
        )
        self.activity = Activity.objects.create(place=self.place, program=self.program, name_az='Local name',
            supplement_az='Local supplement', program_snapshot={'description_az': 'Approved'})
        with override('ru'):
            self.detail_url = reverse('organization_program_detail', args=[self.org.pk, self.program.pk])
            self.save_url = reverse('organization_program_save', args=[self.org.pk, self.program.pk])
        self.client.force_login(self.owner)

    def propose(self, patch=None, submit=True):
        self.program.refresh_from_db()
        revision = getattr(self.program, 'content_revision', None)
        return publication.propose(actor=self.owner, target_type='program', target_id=self.program.pk,
            patch=patch if patch is not None else {'description_az': 'Proposed'},
            schema_version=publication.SCHEMA_VERSION, expected_version=self.program.content_version,
            revision_version=revision.version if revision else 0, submit=submit)

    def decline(self, patch=None, note='Reason OFFER08', final=True):
        revision = self.propose(patch)
        return publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
            approve=False, final_reject=final, note=note)

    def test_declined_owner_sees_reason_and_readonly_proposal_without_live_overlay(self):
        self.decline()
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Reason OFFER08')
        self.assertContains(response, 'data-declined-field="description_az">Proposed')
        self.assertEqual(response.context['form'].initial['description_az'], 'Approved')
        self.assertEqual(response.context['declined_changes'][0]['value'], 'Proposed')
        self.program.refresh_from_db(); self.activity.refresh_from_db()
        self.assertEqual(self.program.description_az, 'Approved')
        self.assertEqual(self.activity.program_snapshot['description_az'], 'Approved')

    def test_return_keeps_proposed_input_and_review_reason(self):
        self.decline(final=False)
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Reason OFFER08')
        self.assertEqual(response.context['form'].initial['description_az'], 'Proposed')
        self.assertNotContains(response, 'data-declined-field=')

    def test_active_draft_and_pending_keep_editable_overlay(self):
        for submit in (False, True):
            with self.subTest(submit=submit):
                self.propose(submit=submit)
                response = self.client.get(self.detail_url)
                self.assertEqual(response.context['form'].initial['description_az'], 'Proposed')
                self.assertNotContains(response, 'org-program-proposal')

    def test_approved_hides_terminal_preview_and_uses_live_text(self):
        revision = self.propose()
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True, note='Accepted')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['form'].initial['description_az'], 'Proposed')
        self.assertNotContains(response, 'org-program-proposal')
        self.assertNotContains(response, 'org-program-decision')

    def test_correction_resubmit_gates_live_and_preserves_local_branch_fields(self):
        revision = self.decline()
        data = self.post_data(revision, description='Corrected')
        self.assertEqual(self.client.post(self.save_url, data).status_code, 302)
        self.program.refresh_from_db(); self.activity.refresh_from_db()
        self.assertEqual(self.program.description_az, 'Approved')
        self.assertEqual(self.activity.program_snapshot['description_az'], 'Approved')
        revision = self.program.content_revision
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(revision.payload['description_az'], 'Corrected')
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.program.refresh_from_db(); self.activity.refresh_from_db()
        self.assertEqual(self.program.description_az, 'Corrected')
        self.assertEqual(self.activity.program_snapshot['description_az'], 'Corrected')
        self.assertEqual(self.activity.name_az, 'Local name')
        self.assertEqual(self.activity.supplement_az, 'Local supplement')

    def post_data(self, revision, description='Typed correction'):
        return {'name_az': self.program.name_az, 'description_az': description,
                'category': self.program.category_id, 'subcategory': self.program.subcategory_id,
                'expected_version': self.program.content_version, 'revision_version': revision.version,
                'impact_confirmed': '1', 'submit': '1'}

    def test_invalid_and_stale_posts_keep_decision_and_bound_input(self):
        revision = self.decline()
        for kind, status in [('impact', 400), ('version', 409)]:
            with self.subTest(kind=kind):
                data = self.post_data(revision)
                if kind == 'impact': data.pop('impact_confirmed')
                else: data['revision_version'] = revision.version - 1
                response = self.client.post(self.save_url, data)
                self.assertEqual(response.status_code, status)
                self.assertContains(response, 'Reason OFFER08', status_code=status)
                self.assertContains(response, 'data-declined-field="description_az">Proposed', status_code=status)
                self.assertEqual(response.context['form']['description_az'].value(), 'Typed correction')
        revision.refresh_from_db(); self.program.refresh_from_db()
        self.assertEqual(revision.status, 'declined')
        self.assertEqual(self.program.description_az, 'Approved')

    def test_outsider_cannot_read_decision_or_submit(self):
        revision = self.decline()
        self.client.force_login(self.outsider)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Reason OFFER08', status_code=404)
        self.assertEqual(self.client.post(self.save_url, self.post_data(revision)).status_code, 404)
        revision.refresh_from_db(); self.assertEqual(revision.status, 'declined')

    def test_reason_and_proposal_are_escaped_and_keep_line_breaks(self):
        unsafe = '<script>window.OFFER08=1</script>\nSecond line'
        self.decline({'description_az': unsafe}, note=unsafe)
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, '<script>window.OFFER08=1</script>')
        self.assertContains(response, escape(unsafe), count=2)
        self.assertEqual(response.context['form'].initial['description_az'], 'Approved')

    def test_null_taxonomy_blank_text_and_unknown_payload_are_safe(self):
        revision = self.decline({'category': None, 'subcategory': None, 'description_ru': ''})
        # Malformed historical JSON must not become rendered controls/private metadata.
        revision.payload['expected_version'] = 'DO_NOT_RENDER_PRIVATE_META'
        revision.save(update_fields=['payload'])
        response = self.client.get(self.detail_url)
        fields = {item['field']: item['value'] for item in response.context['declined_changes']}
        self.assertEqual(fields, {'description_ru': '', 'category': '—', 'subcategory': '—'})
        self.assertNotContains(response, 'DO_NOT_RENDER_PRIVATE_META')
        self.assertEqual(response.context['form'].initial['description_ru'], 'Одобрено')

    def test_taxonomy_preview_uses_localized_names_instead_of_ids(self):
        self.program.category = None; self.program.subcategory = None; self.program.save()
        self.decline({'category': self.place.category_id, 'subcategory': self.place.subcategory_id})
        response = self.client.get(self.detail_url)
        fields = {item['field']: item['value'] for item in response.context['declined_changes']}
        with override('ru'):
            self.assertEqual(fields['category'], self.place.category.name_i18n())
            self.assertEqual(fields['subcategory'], self.place.subcategory.name_i18n())

    def test_declined_labels_are_localized_and_state_specific(self):
        self.decline()
        for language, heading, action in [('ru', 'Отклонённые изменения', 'Отправить новое предложение'),
                ('az', 'İmtina edilmiş dəyişikliklər', 'Yeni təklif göndər'),
                ('en', 'Rejected changes', 'Submit a new proposal')]:
            response = self.client.get(self.detail_url.replace('/ru/', '/' + language + '/'), follow=True)
            self.assertContains(response, heading)
            self.assertContains(response, action)

    def test_empty_declined_draft_does_not_claim_published_content(self):
        self.program.status = 'draft'; self.program.approved_at = None; self.program.save()
        self.decline({'description_az': 'Approved'})
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['declined_changes'], [])
        self.assertContains(response, 'Изменений в отклонённом предложении нет.')
        self.assertContains(response, 'Ниже — текущая версия.')
        self.assertNotContains(response, 'Ниже — текущая опубликованная версия.')
