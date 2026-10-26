from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import ServerDraft
from catalog.services import publication
from catalog.services.place_working_drafts import working_drafts_overview


class DraftReadinessDisplayTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='draft_test_owner',
            email='draft_test@example.com',
            password='TestPassword123!',
        )
        self.draft = ServerDraft.objects.create(
            actor=self.user,
            target_type='place',
            schema_version=publication.SCHEMA_VERSION,
            fields={'name_ru': 'Тестовый черновик робототехники', 'name_az': 'Robototexnika qaralaması'},
        )

    def test_working_drafts_overview_includes_readiness(self):
        overview = working_drafts_overview(user=self.user)
        self.assertEqual(overview['working_drafts_overview_count'], 1)
        card = overview['working_drafts_overview'][0]
        self.assertEqual(card['id'], str(self.draft.pk))
        self.assertIn('readiness', card)
        readiness = card['readiness']
        self.assertIn('percentage', readiness)
        self.assertIn('missing_labels', readiness)
        self.assertGreater(readiness['required_count'], 0)
        self.assertTrue(len(readiness['missing_labels']) > 0)

    def test_account_overview_page_renders_draft_progress_and_chips(self):
        self.client.force_login(self.user)
        response = self.client.get('/ru/account/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('account-draft-row', html)
        self.assertIn('account-draft-missing', html)
        self.assertIn(f'data-working-draft-id="{self.draft.pk}"', html)

    def test_owner_places_dashboard_renders_draft_progress_and_chips(self):
        self.client.force_login(self.user)
        response = self.client.get('/ru/account/places/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('account-owner-card--draft', html)
        self.assertIn('account-draft-missing', html)
        self.assertIn('account-draft-chip', html)
        self.assertIn(f'data-working-draft-id="{self.draft.pk}"', html)
        self.assertIn('data-working-draft-delete', html)
