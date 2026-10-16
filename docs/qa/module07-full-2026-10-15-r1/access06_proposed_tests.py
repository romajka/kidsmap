"""Proposed regression file; QA artifact only until ACCESS06 scope approval."""
import secrets
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation
from catalog.forms import AccountDeletionConfirmForm
from catalog.models import AccountDeletionRequest, UserEmailVerification
from catalog.services.account_deletion import request_account_deletion, typed_confirmation_phrase
from catalog.testcases.test_account_deletion import TEST_POLICY


@override_settings(ACCOUNT_DELETION_RETENTION_POLICY=TEST_POLICY,
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DeletionExactPhraseTests(TestCase):
    def make_request(self, label, language):
        user = get_user_model().objects.create_user(
            username='qa06_' + label, email=label + '@example.invalid', password=None)
        UserEmailVerification.objects.create(
            user=user, email=user.email, is_verified=True, verified_at=timezone.now())
        code = f'{secrets.randbelow(1_000_000):06d}'
        with patch('catalog.services.account_deletion._generate_code', return_value=code):
            deletion = request_account_deletion(user=user, language_code=language)
        self.client.force_login(user)  # Unit setup; native signup/login tested separately.
        with translation.override(language):
            url = reverse('account_deletion_confirm', args=[deletion.subject_reference])
        return user, deletion, code, url

    @staticmethod
    def padded_values(exact):
        return {'leading': ' ' + exact, 'trailing': exact + ' ',
                'both': ' ' + exact + ' ', 'nbsp': '\u00a0' + exact + '\u00a0'}

    def test_form_preserves_exact_input_instead_of_normalizing_it(self):
        for language in ('ru', 'az', 'en'):
            exact = typed_confirmation_phrase(language)
            for kind, raw in self.padded_values(exact).items():
                with self.subTest(language=language, kind=kind):
                    code = f'{secrets.randbelow(1_000_000):06d}'
                    form = AccountDeletionConfirmForm(data={
                        'form_action': 'confirm', 'confirmation_code': code,
                        'typed_confirmation': raw})
                    self.assertTrue(form.is_valid())
                    self.assertTrue(form.cleaned_data['typed_confirmation'] == raw)

    def test_padded_phrase_is_rejected_by_web_and_keeps_account_and_code(self):
        for language in ('ru', 'az', 'en'):
            exact = typed_confirmation_phrase(language)
            for kind, raw in self.padded_values(exact).items():
                with self.subTest(language=language, kind=kind):
                    user, deletion, code, url = self.make_request(language + '_' + kind, language)
                    original_hash = deletion.confirmation_code_hash
                    response = self.client.post(url, {'form_action': 'confirm',
                        'confirmation_code': code, 'typed_confirmation': raw})
                    self.assertEqual(response.status_code, 400)
                    self.assertTrue('typed_confirmation' in response.context['form'].errors)
                    self.assertTrue(response.context['form']['typed_confirmation'].value() == raw)
                    user.refresh_from_db(); deletion.refresh_from_db()
                    self.assertTrue(user.is_active)
                    self.assertEqual(deletion.status, AccountDeletionRequest.Status.CONFIRMATION_SENT)
                    self.assertEqual(deletion.confirmation_attempts_left, 5)
                    self.assertTrue(deletion.confirmation_code_hash == original_hash)

    def test_exact_phrase_with_wrong_code_keeps_existing_code_guard(self):
        for language in ('ru', 'az', 'en'):
            with self.subTest(language=language):
                user, deletion, code, url = self.make_request(language + '_wrong_code', language)
                wrong = f'{(int(code) + 1) % 1_000_000:06d}'
                response = self.client.post(url, {'form_action': 'confirm',
                    'confirmation_code': wrong, 'typed_confirmation': typed_confirmation_phrase(language)})
                self.assertEqual(response.status_code, 400)
                self.assertTrue('confirmation_code' in response.context['form'].errors)
                user.refresh_from_db(); deletion.refresh_from_db()
                self.assertTrue(user.is_active)
                self.assertEqual(deletion.confirmation_attempts_left, 4)

    def test_exact_phrase_and_correct_code_still_schedule_and_end_session(self):
        for language in ('ru', 'az', 'en'):
            with self.subTest(language=language):
                user, deletion, code, url = self.make_request(language + '_exact', language)
                response = self.client.post(url, {'form_action': 'confirm',
                    'confirmation_code': code, 'typed_confirmation': typed_confirmation_phrase(language)})
                self.assertEqual(response.status_code, 302)
                user.refresh_from_db(); deletion.refresh_from_db()
                self.assertFalse(user.is_active)
                self.assertEqual(deletion.status, AccountDeletionRequest.Status.SCHEDULED)
                self.assertFalse(bool(deletion.confirmation_code_hash))
                with translation.override(language):
                    protected = reverse('account_settings')
                self.assertEqual(self.client.get(protected).status_code, 302)
